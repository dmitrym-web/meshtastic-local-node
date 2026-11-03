import os
import time
import meshtastic
from meshtastic.tcp_interface import TCPInterface

TEXT = os.environ["MSG_TEXT"]
CH = int(os.environ.get("CHANNEL_INDEX", "0"))
VN_PORT = int(os.environ.get("MESHMONITOR_VIRTUAL_NODE_PORT", 4404))

MAX_BYTES = 150

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

for i, chunk in enumerate(chunks):
    if i > 0:
        time.sleep(5)
    interface.sendText(chunk, channelIndex=CH)

time.sleep(2)
interface.close()