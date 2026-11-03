import os
import time
import lib

TEXT = os.environ["MSG_TEXT"]
CH = int(os.environ.get("CHANNEL_INDEX", "0"))
MAX_BYTES = int(os.environ.get("MAX_MESSAGE_BYTES", "150"))
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
interface = lib.connect_to_vn()

for i, chunk in enumerate(chunks):
    if i > 0:
        time.sleep(MESSAGE_CHUNK_DELAY)
    interface.sendText(chunk, channelIndex=CH)

time.sleep(SEND_CLOSE_DELAY)
interface.close()