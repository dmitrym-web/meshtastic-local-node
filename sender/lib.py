import os
import sys
from meshtastic.tcp_interface import TCPInterface

def connect_to_vn():
    VN_HOST = os.environ.get("VN_HOST", "localhost")
    VN_PORT = int(os.environ.get("MESHMONITOR_VIRTUAL_NODE_PORT", 4404))

    try:
        return TCPInterface(hostname=VN_HOST, portNumber=VN_PORT)
    except Exception:
        print("Ошибка: сообщение не отправлено. Сервис временно недоступен. Попробуйте позже.", flush=True)
        sys.exit(1)