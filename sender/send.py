import os
import meshtastic.serial_interface
import subprocess

PORT = "/dev/ttyACM0"
TEXT = os.environ["MSG_TEXT"]
CH = 0

subprocess.run(["docker", "stop", "mqtt-proxy"])
interface = meshtastic.serial_interface.SerialInterface(devPath=PORT)
interface.sendText(TEXT, channelIndex=CH)
interface.close()
subprocess.run(["docker", "start", "mqtt-proxy"])
os._exit(0)