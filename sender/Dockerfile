FROM python:3.12-slim

RUN pip install --no-cache-dir meshtastic paho-mqtt

COPY send.py /send.py
COPY set-position.py /set-position.py

CMD ["sleep", "infinity"]