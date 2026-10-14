FROM python:3.12-slim

RUN pip install --no-cache-dir meshtastic pyserial

RUN apt-get update && apt-get install -y cron docker.io && rm -rf /var/lib/apt/lists/*

COPY send.py /send.py
COPY set-position.py /set-position.py
COPY crontab /etc/crontabs/root
RUN chmod +x /send.py /set-position.py

CMD ["cron", "-f"]