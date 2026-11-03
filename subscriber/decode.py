import os
import sys
import time
import threading
import uuid
import paho.mqtt.client as mqtt
from meshtastic.protobuf import mqtt_pb2, mesh_pb2, portnums_pb2
import meshlib

BROKER = os.environ["MQTT_BROKER"]
PORT = int(os.environ.get("MQTT_PORT", 1883))
USERNAME = os.environ["MQTT_USERNAME"]
PASSWORD = os.environ["MQTT_PASSWORD"]
ROOT = os.environ["MQTT_ROOT_TOPIC"]
CHANNEL_NAME = os.environ.get("CHANNEL", "LongFast")
CHANNEL_KEY = os.environ.get("CHANNEL_KEY", "AQ==")
CHANNEL_KEY_DIRECT = os.environ.get("CHANNEL_KEY_DIRECT", "")
CACHE_FILE = os.environ.get("NODES_CACHE_FILE", "/data/nodes.json")
KEEPALIVE = int(os.environ.get("MQTT_KEEPALIVE", "10"))
WATCHDOG_CHECK_INTERVAL = int(os.environ.get("WATCHDOG_CHECK_INTERVAL", "1"))

LOG_TEXT     = os.environ.get("LOG_TEXT", "true").lower() == "true"
LOG_POSITION = os.environ.get("LOG_POSITION", "true").lower() == "true"
LOG_TELEMETRY= os.environ.get("LOG_TELEMETRY", "false").lower() == "true"
LOG_NODEINFO = os.environ.get("LOG_NODEINFO", "true").lower() == "true"

WATCHDOG_ENABLED = os.environ.get("MQTT_WATCHDOG_ENABLED", "true").lower() == "true"
WATCHDOG_TIMEOUT = int(os.environ.get("MQTT_WATCHDOG_TIMEOUT", "300"))

NODES = meshlib.load_cache(CACHE_FILE)
is_connected = False
disconnect_time = time.time()

def log_sys(msg, color=""):
    t = meshlib.get_time()
    end_color = "\033[0m" if color else ""
    print(f"{color}[{t}] {msg}{end_color}", flush=True)

def on_connect(client, userdata, flags, reason_code, properties=None):
    global is_connected, disconnect_time
    if reason_code == 0:
        is_connected = True
        disconnect_time = None
        topic = f"{ROOT}/2/e/{CHANNEL_NAME}/#"
        client.subscribe(topic)
        log_sys(f"Подписка на {topic}")
    else:
        log_sys(f"Ошибка подключения, код: {reason_code}.")
        is_connected = False
        if disconnect_time is None:
            disconnect_time = time.time()

def on_disconnect(client, userdata, flags, reason_code, properties=None):
    global is_connected, disconnect_time
    if not is_connected:
        return
    is_connected = False
    if disconnect_time is None:
        disconnect_time = time.time()
    if getattr(reason_code, 'value', reason_code) != 0:
        log_sys(f"Отключено от брокера! Код причины: {reason_code}.")

def watchdog():
    while True:
        time.sleep(WATCHDOG_CHECK_INTERVAL)
        if not WATCHDOG_ENABLED:
            continue
        if not is_connected and disconnect_time:
            if time.time() - disconnect_time > WATCHDOG_TIMEOUT:
                log_sys(f"КРИТИЧНО: Соединение с MQTT потеряно более {WATCHDOG_TIMEOUT} секунд. Перезапуск...", "\033[31m")
                time.sleep(1)
                sys.exit(1)

def on_message(client, userdata, msg):
    try:
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.ParseFromString(msg.payload)
        packet = envelope.packet

        if packet.HasField("encrypted"):
            data, _ = meshlib.decrypt_packet(packet, CHANNEL_KEY, CHANNEL_KEY_DIRECT)
        else:
            data = packet.decoded

        if data is None:
            return

        from_node = getattr(packet, "from")
        sender = meshlib.get_node_label(from_node, NODES)

        if data.portnum == portnums_pb2.PortNum.NODEINFO_APP:
            user = mesh_pb2.User()
            user.ParseFromString(data.payload)
            name = user.long_name or user.short_name
            if name and NODES.get(from_node) != name:
                NODES[from_node] = name
                meshlib.save_cache(CACHE_FILE, NODES)
            if LOG_NODEINFO:
                t = meshlib.get_time()
                print(f"[{t}] [{CHANNEL_NAME}] {sender}: NODEINFO ({name})", flush=True)
                
        elif data.portnum == portnums_pb2.PortNum.TEXT_MESSAGE_APP:
            if LOG_TEXT:
                text = data.payload.decode("utf-8", errors="replace")
                t = meshlib.get_time()
                print(f"[{t}] [{CHANNEL_NAME}] {sender}: {text}", flush=True)
                
        elif data.portnum == portnums_pb2.PortNum.POSITION_APP:
            if LOG_POSITION:
                t = meshlib.get_time()
                print(f"[{t}] [{CHANNEL_NAME}] {sender}: POSITION", flush=True)
                
        elif data.portnum == portnums_pb2.PortNum.TELEMETRY_APP:
            if LOG_TELEMETRY:
                t = meshlib.get_time()
                print(f"[{t}] [{CHANNEL_NAME}] {sender}: TELEMETRY", flush=True)
                
    except Exception as e:
        log_sys(f"Ошибка расшифровки: {e}")

client_id = f"dec-{uuid.uuid4().hex[:8]}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, clean_session=False)
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.connect(BROKER, PORT, KEEPALIVE)

threading.Thread(target=watchdog, daemon=True).start()
client.loop_forever()