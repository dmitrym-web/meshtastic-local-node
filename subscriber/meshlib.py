import os
import json
import base64
from datetime import datetime
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from meshtastic.protobuf import mesh_pb2
from meshtastic.util import fromPSK

def get_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def load_cache(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception as e:
            print(f"Ошибка загрузки кэша: {e}", flush=True)
    return {}

def save_cache(filepath, nodes):
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(nodes, f)
        st = os.stat(os.path.dirname(filepath))
        os.chown(filepath, st.st_uid, st.st_gid)
    except Exception as e:
        print(f"Ошибка сохранения кэша: {e}", flush=True)

def decrypt_packet(packet, channel_key, direct_key=None):
    fn = getattr(packet, "from")
    to = packet.to
    pid = packet.id
    enc = packet.encrypted

    keys = [("psk", base64.b64decode(fromPSK(channel_key)))]
    if direct_key:
        keys.append(("dir", base64.b64decode(direct_key)))

    nonces = [
        ("id+from", pid.to_bytes(8, "little") + fn.to_bytes(8, "little")),
        ("id+to", pid.to_bytes(8, "little") + to.to_bytes(8, "little")),
    ]

    for nlabel, nonce in nonces:
        for klabel, key in keys:
            try:
                c = Cipher(algorithms.AES(key), modes.CTR(nonce), backend=default_backend())
                d = c.decryptor()
                raw = d.update(enc) + d.finalize()
                data = mesh_pb2.Data()
                data.ParseFromString(raw)
                if data.portnum:
                    return data, f"{nlabel}/{klabel}"
            except Exception:
                continue
    return None, None

def get_node_label(node_id, nodes):
    return nodes.get(node_id) or f"!{node_id:08x}"