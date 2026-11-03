import os
import time
import meshtastic
from meshtastic.tcp_interface import TCPInterface

TEXT = os.environ["MSG_TEXT"]
CH = int(os.environ.get("CHANNEL_INDEX", "0"))
VN_HOST = os.environ.get("VN_HOST", "localhost")
VN_PORT = int(os.environ.get("MESHMONITOR_VIRTUAL_NODE_PORT", 4404))
MAX_BYTES = int(os.environ.get("MAX_MESSAGE_BYTES", "150"))

VN_RETRY_COUNT = int(os.environ.get("VN_RETRY_COUNT", "24"))
VN_RETRY_DELAY = int(os.environ.get("VN_RETRY_DELAY", "5"))
MESSAGE_CHUNK_DELAY = int(os.environ.get("MESSAGE_CHUNK_DELAY", "5"))
SEND_CLOSE_DELAY = int(os.environ.get("SEND_CLOSE_DELAY", "2"))

def split_text(text, max_bytes):
    chunks = []
    while text:
        if len(text.encode('utf-8')) <= max_bytes:
            chunks.append(text)
            break
        
        current_bytes = 0
        cut_index = 0
        for i, char in enumerate(text):
            char_len = len(char.encode('utf-8'))
            if current_bytes + char_len > max_bytes:
                break
            current_bytes += char_len
            cut_index = i + 1
        
        chunk = text[:cut_index]
        last_space = chunk.rfind(' ')
        if last_space > 0:
            chunk = chunk[:last_space]
            text = text[len(chunk):].lstrip()
        else:
            text = text[cut_index:]
        
        if chunk:
            chunks.append(chunk)
    return chunks

chunks = split_text(TEXT, MAX_BYTES)

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

for i, chunk in enumerate(chunks):
    if i > 0:
        time.sleep(MESSAGE_CHUNK_DELAY)
    interface.sendText(chunk, channelIndex=CH)

time.sleep(SEND_CLOSE_DELAY)
interface.close()