#!/bin/bash

PORTS=$(ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true)
if [ -z "$PORTS" ]; then
  echo "Ошибка: нода не найдена. Убедитесь, что устройство подключено. Настройки .env не изменены." >&2
  exit 1
fi

PORTS_ARRAY=($PORTS)
COUNT=${#PORTS_ARRAY[@]}

if [ "$COUNT" -eq 1 ]; then
  PORT="${PORTS_ARRAY[0]}"
else
  echo "Найдено устройств: $COUNT" >&2
  for i in "${!PORTS_ARRAY[@]}"; do
    echo "  $((i+1))) ${PORTS_ARRAY[$i]}" >&2
  done
  while true; do
    echo -n "Выбери порт (1-$COUNT): " >&2
    read -r CHOICE
    if [[ "$CHOICE" =~ ^[0-9]+$ ]] && [ "$CHOICE" -ge 1 ] && [ "$CHOICE" -le "$COUNT" ]; then
      PORT="${PORTS_ARRAY[$((CHOICE-1))]}"
      break
    fi
    echo "Неверный номер." >&2
  done
fi

echo "Получение ID ноды..." >&2
INFO=$(meshtastic --port "$PORT" --info 2>/dev/null)
NODE_ID=$(echo "$INFO" | grep -oE '![0-9a-f]{8}' | head -1)

if [ -n "$NODE_ID" ]; then
  echo "SERIAL_PORT=$PORT"
  echo "NODE_ID=$NODE_ID"
else
  echo "Ошибка: устройство найдено, но не отвечает. Возможно, порт занят. Выполните 'make down' и повторите попытку." >&2
  exit 1
fi