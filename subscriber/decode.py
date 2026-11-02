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

BROKER = os.environ["MQTT_BROKER"]
PORT = int(os.environ.get("MQTT_PORT", 1883))
USERNAME = os.environ["MQTT_USERNAME"]
PASSWORD = os.environ["MQTT_PASSWORD"]
ROOT = os.environ["MQTT_ROOT_TOPIC"]
CHANNEL_NAME = os.environ.get("CHANNEL", "LongFast")
CHANNEL_KEY = os.environ.get("CHANNEL_KEY", "AQ==")

LOG_TEXT     = os.environ.get("LOG_TEXT", "true").lower() == "true"
LOG_POSITION = os.environ.get("LOG_POSITION", "true").lower() == "true"
LOG_TELEMETRY= os.environ.get("LOG_TELEMETRY", "false").lower() == "true"
LOG_NODEINFO = os.environ.get("LOG_NODEINFO", "true").lower() == "true"

WATCHDOG_ENABLED = os.environ.get("MQTT_WATCHDOG_ENABLED", "true").lower() == "true"
WATCHDOG_TIMEOUT = int(os.environ.get("MQTT_WATCHDOG_TIMEOUT", "300"))
RECONNECT_MAX_DELAY = int(os.environ.get("MQTT_RECONNECT_MAX_DELAY", "10"))

KEY = fromPSK(CHANNEL_KEY)
CACHE_FILE = "/data/nodes.json"
NODES = {}

is_connected = False
disconnect_time = time.time()

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def log_sys(msg, color=""):
    t = get_time()
    end_color = "\033[0m" if color else ""
    print(f"{color}[{t}] {msg}{end_color}", flush=True)

def load_cache():
    global NODES
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                NODES = {int(k): v for k, v in data.items()}
        except Exception as e:
            log_sys(f"Cache load error: {e}")
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
        log_sys(f"Cache save error: {e}")

def decrypt_packet(mesh_packet):
    key_bytes = base64.b64decode(KEY)
    from_node = getattr(mesh_packet, "from")
    packet_id = getattr(mesh_packet, "id")
    nonce = packet_id.to_bytes(8, "little") + from_node.to_bytes(8, "little")
    cipher = Cipher(algorithms.AES(key_bytes), modes.CTR(nonce), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted_bytes = decryptor.update(getattr(mesh_packet, "encrypted")) + decryptor.finalize()
    data = mesh_pb2.Data()
    data.ParseFromString(decrypted_bytes)
    return data

def node_label(from_node):
    name = NODES.get(from_node)
    if name:
        return name
    return f"!{from_node:08x}"

def on_connect(client, userdata, flags, reason_code, properties=None):
    global is_connected, disconnect_time
    if reason_code == 0:
        is_connected = True
        disconnect_time = None
        topic = f"{ROOT}/2/e/{CHANNEL_NAME}/#"
        client.subscribe(topic)
        log_sys(f"Subscribed to {topic}")
    else:
        log_sys(f"Connection failed with code: {reason_code}.")
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
        log_sys(f"Disconnected from broker! Reason code: {reason_code}.")

def watchdog():
    while True:
        time.sleep(1)
        if not WATCHDOG_ENABLED:
            continue
        if not is_connected and disconnect_time:
            if time.time() - disconnect_time > WATCHDOG_TIMEOUT:
                log_sys(f"CRITICAL: MQTT connection lost for {WATCHDOG_TIMEOUT} seconds. Exiting for restart...", "\033[31m")
                time.sleep(1)
                sys.exit(1)

def on_message(client, userdata, msg):
    try:
        envelope = mqtt_pb2.ServiceEnvelope()
        envelope.ParseFromString(msg.payload)
        packet = envelope.packet

        if packet.HasField("encrypted"):
            data = decrypt_packet(packet)
        else:
            data = packet.decoded

        from_node = getattr(packet, "from")
        sender = node_label(from_node)

        if data.portnum == portnums_pb2.PortNum.NODEINFO_APP:
            user = mesh_pb2.User()
            user.ParseFromString(data.payload)
            name = user.long_name or user.short_name
            if name and NODES.get(from_node) != name:
                NODES[from_node] = name
                save_cache()
            if LOG_NODEINFO:
                t = get_time()
                print(f"[{t}] [{CHANNEL_NAME}] {sender}: NODEINFO ({name})", flush=True)
                
        elif data.portnum == portnums_pb2.PortNum.TEXT_MESSAGE_APP:
            if LOG_TEXT:
                text = data.payload.decode("utf-8", errors="replace")
                t = get_time()
                print(f"[{t}] [{CHANNEL_NAME}] {sender}: {text}", flush=True)
                
        elif data.portnum == portnums_pb2.PortNum.POSITION_APP:
            if LOG_POSITION:
                t = get_time()
                print(f"[{t}] [{CHANNEL_NAME}] {sender}: POSITION", flush=True)
                
        elif data.portnum == portnums_pb2.PortNum.TELEMETRY_APP:
            if LOG_TELEMETRY:
                t = get_time()
                print(f"[{t}] [{CHANNEL_NAME}] {sender}: TELEMETRY", flush=True)
                
    except Exception as e:
        log_sys(f"Decode error: {e}")

load_cache()

client_id = f"dec-{uuid.uuid4().hex[:8]}"
client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=client_id, clean_session=False)
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_disconnect = on_disconnect
client.on_message = on_message
client.reconnect_delay_set(min_delay=1, max_delay=RECONNECT_MAX_DELAY)
client.connect(BROKER, PORT, 10)

threading.Thread(target=watchdog, daemon=True).start()
client.loop_forever()