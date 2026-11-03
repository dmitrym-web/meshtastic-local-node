import os
import time
import threading
import uuid
import paho.mqtt.client as mqtt
from meshtastic.protobuf import mqtt_pb2, mesh_pb2, portnums_pb2
import meshlib

BROKER      = os.environ["MQTT_BROKER"]
PORT        = int(os.environ.get("MQTT_PORT", 1883))
USERNAME    = os.environ["MQTT_USERNAME"]
PASSWORD    = os.environ["MQTT_PASSWORD"]
ROOT        = os.environ["MQTT_ROOT_TOPIC"]
CHANNEL     = os.environ.get("CHANNEL", "LongFast")
CHANNEL_KEY = os.environ.get("CHANNEL_KEY", "AQ==")
CHANNEL_KEY_DIRECT = os.environ.get("CHANNEL_KEY_DIRECT", "")
CACHE_FILE = os.environ.get("NODES_CACHE_FILE", "/data/nodes.json")
NODE_ID     = os.environ.get("NODE_ID", "")
KEEPALIVE   = int(os.environ.get("MQTT_KEEPALIVE", "10"))
WATCHDOG_CHECK_INTERVAL = int(os.environ.get("WATCHDOG_CHECK_INTERVAL", "1"))

LOG_TEXT     = os.environ.get("LOG_TEXT", "true").lower() == "true"
LOG_POSITION = os.environ.get("LOG_POSITION", "true").lower() == "true"
LOG_TELEMETRY= os.environ.get("LOG_TELEMETRY", "false").lower() == "true"
LOG_NODEINFO = os.environ.get("LOG_NODEINFO", "true").lower() == "true"

WATCHDOG_ENABLED = os.environ.get("MQTT_WATCHDOG_ENABLED", "true").lower() == "true"
WATCHDOG_TIMEOUT = int(os.environ.get("MQTT_WATCHDOG_TIMEOUT", "300"))

R = "\033[0m"; B = "\033[1m"; D = "\033[2m"
G = "\033[32m"; BL = "\033[34m"; Y = "\033[33m"
C = "\033[36m"; RD = "\033[31m"

NODES = meshlib.load_cache(CACHE_FILE)
is_connected = False
disconnect_time = time.time()
warning_shown = False

def out(direction, sender, text, extra=""):
    t = meshlib.get_time()
    if direction == "out":
        arrow, tag = f"{BL}→{R}", f"{BL}RF  {R}"
    else:
        arrow, tag = f"{G}←{R}", f"{G}MQTT{R}"
    print(f"{D}{t}{R} {tag} {arrow} {B}{sender:<12}{R} {text} {D}{extra}{R}", flush=True)

def on_connect(c, u, f, rc, p=None):
    global is_connected, disconnect_time, warning_shown
    if rc == 0:
        is_connected = True
        disconnect_time = None
        warning_shown = False
        topic = f"{ROOT}/2/e/{CHANNEL}/#"
        c.subscribe(topic)
        t = meshlib.get_time()
        print(f"{C}[{t}] Прослушивание {topic}{R}")
        print(f"{D}[{t}] NODE_ID={NODE_ID}{R}\n")
    else:
        t = meshlib.get_time()
        print(f"{RD}[{t}] Ошибка подключения, код: {rc}{R}", flush=True)
        is_connected = False
        if disconnect_time is None:
            disconnect_time = time.time()

def on_disconnect(c, u, f, rc, p=None):
    global is_connected, disconnect_time
    if not is_connected:
        return
    is_connected = False
    if disconnect_time is None:
        disconnect_time = time.time()
    if getattr(rc, 'value', rc) != 0:
        t = meshlib.get_time()
        print(f"{RD}[{t}] Отключено от брокера! Код причины: {rc}{R}", flush=True)

def watchdog():
    global warning_shown
    while True:
        time.sleep(WATCHDOG_CHECK_INTERVAL)
        if not WATCHDOG_ENABLED:
            continue
        if not is_connected and disconnect_time:
            if time.time() - disconnect_time > WATCHDOG_TIMEOUT:
                if not warning_shown:
                    t = meshlib.get_time()
                    print(f"\n{RD}[{t}] Соединение с брокером потеряно более {WATCHDOG_TIMEOUT} секунд!{R}", flush=True)
                    warning_shown = True

def on_message(c, u, msg):
    try:
        env = mqtt_pb2.ServiceEnvelope()
        env.ParseFromString(msg.payload)
        pkt = env.packet

        direction = "out" if (NODE_ID and env.gateway_id == NODE_ID) else "in"
        from_node = getattr(pkt, "from")
        sender = meshlib.get_node_label(from_node, NODES)

        if pkt.HasField("encrypted"):
            data, how = meshlib.decrypt_packet(pkt, CHANNEL_KEY, CHANNEL_KEY_DIRECT)
            if data is None:
                out(direction, sender, f"{Y}<unable to decrypt>{R}", f"size={len(msg.payload)}")
                return
            extra = f"via={how}"
        elif pkt.HasField("decoded"):
            data = pkt.decoded
            extra = ""
        else:
            return

        pn = data.portnum
        
        if pn == portnums_pb2.PortNum.TEXT_MESSAGE_APP:
            if LOG_TEXT:
                out(direction, sender, data.payload.decode("utf-8", errors="replace"), extra)
                
        elif pn == portnums_pb2.PortNum.NODEINFO_APP:
            user = mesh_pb2.User()
            user.ParseFromString(data.payload)
            name = user.long_name or user.short_name
            if name and NODES.get(from_node) != name:
                NODES[from_node] = name
                meshlib.save_cache(CACHE_FILE, NODES)
            if LOG_NODEINFO:
                out(direction, sender, f"{D}NODEINFO{R} {name or ''}", extra)
                
        elif pn == portnums_pb2.PortNum.POSITION_APP:
            if LOG_POSITION:
                pos = mesh_pb2.Position()
                pos.ParseFromString(data.payload)
                out(direction, sender, f"{D}POSITION {pos.latitude_i/1e7:.5f},{pos.longitude_i/1e7:.5f}{R}", extra)
                
        elif pn == portnums_pb2.PortNum.TELEMETRY_APP:
            if LOG_TELEMETRY:
                out(direction, sender, f"{D}TELEMETRY{R}", extra)
                
    except Exception as e:
        print(f"{RD}[{meshlib.get_time()}] Ошибка парсинга: {e}{R}", flush=True)

client_id = f"mon-{uuid.uuid4().hex[:8]}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, clean_session=False)
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.connect(BROKER, PORT, KEEPALIVE)

threading.Thread(target=watchdog, daemon=True).start()

try:
    client.loop_forever()
except KeyboardInterrupt:
    print(f"\n{C}[{meshlib.get_time()}] Остановлено{R}")
finally:
    client.disconnect()