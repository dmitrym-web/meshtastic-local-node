#!/bin/sh
mosquitto_pub \
  -h "$MQTT_BROKER" \
  -p "$MQTT_PORT" \
  -u "$MQTT_USERNAME" \
  -P "$MQTT_PASSWORD" \
  -t "$MQTT_ROOT_TOPIC/2/json/$CHANNEL/" \
  -m '{"type":"sendtext","payload":"Привет по расписанию!","channel":0,"to":4294967295}'