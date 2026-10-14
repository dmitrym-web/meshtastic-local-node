FROM python:3.12-slim

RUN pip install --no-cache-dir paho-mqtt meshtastic cryptography

COPY decode.py /decode.py

CMD ["python3", "/decode.py"]