FROM python:3.12-slim

RUN apt-get update && apt-get install -y tzdata && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir meshtastic paho-mqtt apscheduler

COPY send.py /send.py
COPY set-position.py /set-position.py
COPY scheduler.py /scheduler.py

CMD ["python3", "-u", "/scheduler.py"]