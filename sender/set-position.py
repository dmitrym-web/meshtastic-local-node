import os
import sys
import time
import lib

lat = float(sys.argv[1])
lon = float(sys.argv[2])
alt = int(sys.argv[3]) if len(sys.argv) > 3 else 0

SEND_CLOSE_DELAY = int(os.environ.get("SEND_CLOSE_DELAY", "2"))

interface = lib.connect_to_vn()

interface.getNode("^local").setFixedPosition(lat, lon, alt)
time.sleep(SEND_CLOSE_DELAY)
interface.close()

print(f"Координаты установлены: {lat}, {lon}, {alt}")