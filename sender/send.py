import os
import time
import paho.mqtt.client as mqtt
import meshtastic
from meshtastic.tcp_interface import TCPInterface

TEXT = os.environ["MSG_TEXT"]
CH = int(os.environ.get("CHANNEL_INDEX", "0"))
BROKER = os.environ["MQTT_BROKER"]
MQTT_PORT = int(os.environ.get("MQTT_PORT", 1883))
USERNAME = os.environ["MQTT_USERNAME"]
PASSWORD = os.environ["MQTT_PASSWORD"]
ROOT = os.environ["MQTT_ROOT_TOPIC"]
NODE_ID = os.environ.get("NODE_ID", "")
VN_PORT = int(os.environ.get("MESHMONITOR_VIRTUAL_NODE_PORT", 4404))

log_topic = f"{ROOT}/2/local/sent"

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.username_pw_set(USERNAME, PASSWORD)
client.connect(BROKER, MQTT_PORT, 60)
client.loop_start()
client.publish(log_topic, f"{NODE_ID}|{TEXT}".encode(), qos=1)
time.sleep(0.5)
client.loop_stop()
client.disconnect()

interface = None
for _ in range(24):
    try:
        interface = TCPInterface(hostname="localhost", portNumber=VN_PORT)
        break
    except meshtastic.mesh_interface.MeshInterface.MeshInterfaceError as e:
        if "Timed out" in str(e) or "Connection refused" in str(e):
            print("Ожидание готовности MeshMonitor (5 сек)...")
            time.sleep(5)
        else:
            raise e

if not interface:
    raise Exception("Не удалось подключиться к MeshMonitor")

interface.sendText(TEXT, channelIndex=CH)
time.sleep(2)
interface.close()