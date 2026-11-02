import os
import sys
import json
import base64
import uuid
import time
import threading
from datetime import datetime
import paho.mqtt.client as mqtt
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from meshtastic.protobuf import mqtt_pb2, mesh_pb2, portnums_pb2
from meshtastic.util import fromPSK

BROKER      = os.environ["MQTT_BROKER"]
PORT        = int(os.environ.get("MQTT_PORT", 1883))
USERNAME    = os.environ["MQTT_USERNAME"]
PASSWORD    = os.environ["MQTT_PASSWORD"]
ROOT        = os.environ["MQTT_ROOT_TOPIC"]
CHANNEL     = os.environ.get("CHANNEL", "LongFast")
CHANNEL_KEY = os.environ.get("CHANNEL_KEY", "AQ==")
NODE_ID     = os.environ.get("NODE_ID", "")

LOG_TEXT     = os.environ.get("LOG_TEXT", "true").lower() == "true"
LOG_POSITION = os.environ.get("LOG_POSITION", "true").lower() == "true"
LOG_TELEMETRY= os.environ.get("LOG_TELEMETRY", "false").lower() == "true"
LOG_NODEINFO = os.environ.get("LOG_NODEINFO", "true").lower() == "true"

WATCHDOG_ENABLED = os.environ.get("MQTT_WATCHDOG_ENABLED", "true").lower() == "true"
WATCHDOG_TIMEOUT = int(os.environ.get("MQTT_WATCHDOG_TIMEOUT", "300"))
RECONNECT_MAX_DELAY = int(os.environ.get("MQTT_RECONNECT_MAX_DELAY", "10"))

KEY_FROM_PSK = base64.b64decode(fromPSK(CHANNEL_KEY))
KEY_DIRECT   = base64.b64decode("1PG7OiApB1nwvP+rz05pAQ==")

R = "\033[0m"; B = "\033[1m"; D = "\033[2m"
G = "\033[32m"; BL = "\033[34m"; Y = "\033[33m"
C = "\033[36m"; RD = "\033[31m"

CACHE_FILE = "/data/nodes.json"
NODES = {}

is_connected = False
disconnect_time = time.time()
warning_shown = False

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_cache():
    global NODES
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                NODES = {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"{RD}[{get_time()}] Cache load error: {e}{R}", flush=True)
    else:
        save_cache()

def save_cache():
    try:
        os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(NODES, f)
        st = os.stat("/data")
        os.chown(CACHE_FILE, st.st_uid, st.st_gid)
    except Exception as e:
        print(f"{RD}[{get_time()}] Cache save error: {e}{R}", flush=True)

def decrypt(mp):
    fn  = getattr(mp, "from")
    to  = mp.to
    pid = mp.id
    enc = mp.encrypted
    nonces = [
        ("id+from", pid.to_bytes(8, "little") + fn.to_bytes(8, "little")),
        ("id+to",   pid.to_bytes(8, "little") + to.to_bytes(8, "little")),
    ]
    keys = [("psk", KEY_FROM_PSK), ("dir", KEY_DIRECT)]
    for nlabel, nonce in nonces:
        for klabel, key in keys:
            try:
                c = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
                d = c.decryptor()
                raw = d.update(enc) + d.finalize()
                data = mesh_pb2.Data()
                data.ParseFromString(raw)
                if data.portnum:
                    return data, f"{nlabel}/{klabel}"
            except Exception:
                continue
    return None, None

def label(num):
    return NODES.get(num) or f"!{num:08x}"

def out(direction, sender, text, extra=""):
    t = get_time()
    if direction == "out":
        arrow, tag = f"{BL}→{R}", f"{BL}OUT{R}"
    else:
        arrow, tag = f"{G}←{R}", f"{G}IN {R}"
    print(f"{D}{t}{R} {tag} {arrow} {B}{sender:<12}{R} {text} {D}{extra}{R}", flush=True)

def on_connect(c, u, f, rc, p=None):
    global is_connected, disconnect_time, warning_shown
    if rc == 0:
        is_connected = True
        disconnect_time = None
        warning_shown = False
        topic = f"{ROOT}/2/e/{CHANNEL}/#"
        log_topic = f"{ROOT}/2/local/sent"
        c.subscribe(topic)
        c.subscribe(log_topic)
        t = get_time()
        print(f"{C}[{t}] Listening on {topic}{R}")
        print(f"{C}[{t}] Listening on {log_topic}{R}")
        print(f"{D}[{t}] NODE_ID={NODE_ID}{R}\n")
    else:
        t = get_time()
        print(f"{RD}[{t}] Connection failed with code {rc}{R}", flush=True)
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
        t = get_time()
        print(f"{RD}[{t}] Disconnected from broker! Reason code: {rc}{R}", flush=True)

def watchdog():
    global warning_shown
    while True:
        time.sleep(1)
        if not WATCHDOG_ENABLED:
            continue
        if not is_connected and disconnect_time:
            if time.time() - disconnect_time > WATCHDOG_TIMEOUT:
                if not warning_shown:
                    t = get_time()
                    print(f"\n{RD}[{t}] Соединение с брокером потеряно более {WATCHDOG_TIMEOUT} секунд!{R}", flush=True)
                    warning_shown = True

def on_message(c, u, msg):
    if msg.topic.endswith("/local/sent"):
        try:
            body = msg.payload.decode("utf-8", errors="replace")
            node, _, text = body.partition("|")
            sender = NODES.get(node) or node
            out("out", sender, text, "via=sender-log")
        except Exception as e:
            print(f"{RD}[{get_time()}] log parse error: {e}{R}", flush=True)
        return

    try:
        env = mqtt_pb2.ServiceEnvelope()
        env.ParseFromString(msg.payload)
        pkt = env.packet

        direction = "out" if (NODE_ID and env.gateway_id == NODE_ID) else "in"
        from_node = getattr(pkt, "from")
        sender = label(from_node)

        if pkt.HasField("encrypted"):
            data, how = decrypt(pkt)
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
                save_cache()
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
        print(f"{RD}[{get_time()}] parse error: {e}{R}", flush=True)

load_cache()

client_id = f"mon-{uuid.uuid4().hex[:8]}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, clean_session=False)
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.reconnect_delay_set(min_delay=1, max_delay=RECONNECT_MAX_DELAY)
client.connect(BROKER, PORT, 10)

threading.Thread(target=watchdog, daemon=True).start()

try:
    client.loop_forever()
except KeyboardInterrupt:
    print(f"\n{C}[{get_time()}] stopped{R}")
finally:
    client.disconnect()