import os
import sys
import time
import meshtastic
from meshtastic.tcp_interface import TCPInterface

lat = float(sys.argv[1])
lon = float(sys.argv[2])
alt = int(sys.argv[3]) if len(sys.argv) > 3 else 0

VN_HOST = os.environ.get("VN_HOST", "localhost")
VN_PORT = int(os.environ.get("MESHMONITOR_VIRTUAL_NODE_PORT", 4404))
VN_RETRY_COUNT = int(os.environ.get("VN_RETRY_COUNT", "24"))
VN_RETRY_DELAY = int(os.environ.get("VN_RETRY_DELAY", "5"))
SEND_CLOSE_DELAY = int(os.environ.get("SEND_CLOSE_DELAY", "2"))

interface = None
for _ in range(VN_RETRY_COUNT):
    try:
        interface = TCPInterface(hostname=VN_HOST, portNumber=VN_PORT)
        break
    except meshtastic.mesh_interface.MeshInterface.MeshInterfaceError as e:
        if "Timed out" in str(e) or "Connection refused" in str(e):
            print(f"Ожидание готовности MeshMonitor ({VN_RETRY_DELAY} сек)...")
            time.sleep(VN_RETRY_DELAY)
        else:
            raise e

if not interface:
    raise Exception("Не удалось подключиться к MeshMonitor")

interface.getNode("^local").setFixedPosition(lat, lon, alt)
time.sleep(SEND_CLOSE_DELAY)
interface.close()

print(f"Координаты установлены: {lat}, {lon}, {alt}")