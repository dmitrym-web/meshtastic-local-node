import os
import sys
import time
import meshtastic
from meshtastic.tcp_interface import TCPInterface

lat = float(sys.argv[1])
lon = float(sys.argv[2])
alt = int(sys.argv[3]) if len(sys.argv) > 3 else 0
VN_PORT = int(os.environ.get("MESHMONITOR_VIRTUAL_NODE_PORT", 4404))

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

interface.getNode("^local").setFixedPosition(lat, lon, alt)
time.sleep(2)
interface.close()

print(f"Координаты установлены: {lat}, {lon}, {alt}")