import os
import base64
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

KEY = fromPSK(CHANNEL_KEY)

NODES = {}


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
    topic = f"{ROOT}/2/e/{CHANNEL_NAME}/#"
    client.subscribe(topic)
    print(f"Subscribed to {topic}", flush=True)


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
            if name:
                NODES[from_node] = name
                print(f"[{CHANNEL_NAME}] {sender}: NODEINFO ({name})", flush=True)
            else:
                print(f"[{CHANNEL_NAME}] {sender}: NODEINFO", flush=True)
        elif data.portnum == portnums_pb2.PortNum.TEXT_MESSAGE_APP:
            text = data.payload.decode("utf-8", errors="replace")
            print(f"[{CHANNEL_NAME}] {sender}: {text}", flush=True)
        elif data.portnum == portnums_pb2.PortNum.POSITION_APP:
            print(f"[{CHANNEL_NAME}] {sender}: POSITION", flush=True)
        elif data.portnum == portnums_pb2.PortNum.TELEMETRY_APP:
            print(f"[{CHANNEL_NAME}] {sender}: TELEMETRY", flush=True)
        else:
            name = portnums_pb2.PortNum.Name(data.portnum)
            print(f"[{CHANNEL_NAME}] {sender}: {name}", flush=True)
    except Exception as e:
        print(f"Decode error: {e}", flush=True)


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USERNAME, PASSWORD)
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.loop_forever()