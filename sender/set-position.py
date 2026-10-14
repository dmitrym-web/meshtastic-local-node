import subprocess
import sys
import meshtastic.serial_interface

PORT = "/dev/ttyACM0"

lat = float(sys.argv[1])
lon = float(sys.argv[2])
alt = int(sys.argv[3]) if len(sys.argv) > 3 else 0

subprocess.run(["docker", "stop", "mqtt-proxy"])

try:
    interface = meshtastic.serial_interface.SerialInterface(devPath=PORT)
    interface.getNode("^local").setFixedPosition(lat, lon, alt)
    interface.close()
finally:
    subprocess.run(["docker", "start", "mqtt-proxy"])

print(f"Координаты установлены: {lat}, {lon}, {alt}")