#!/bin/bash

if ! command -v meshtastic >/dev/null 2>&1; then
  echo "meshtastic CLI не найден в PATH."
  exit 1
fi

PORTS=$(ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true)
if [ -z "$PORTS" ]; then
  echo "USB-порты не найдены."
  exit 1
fi

VALID_PORTS=()
VALID_IDS=()
VALID_NAMES=()

for p in $PORTS; do
  INFO=$(meshtastic --port "$p" --info 2>/dev/null)
  NODE_ID=$(echo "$INFO" | grep -oE '![0-9a-f]{8}' | head -1)
  if [ -z "$NODE_ID" ]; then
    continue
  fi
  NAME=$(echo "$INFO" | grep -oE 'Owner: [^(]+' | head -1 | sed 's/Owner: *//; s/ *$//')
  VALID_PORTS+=("$p")
  VALID_IDS+=("$NODE_ID")
  VALID_NAMES+=("$NAME")
done

COUNT=${#VALID_PORTS[@]}

if [ "$COUNT" -eq 0 ]; then
  echo "Meshtastic-ноды не найдены."
  exit 1
fi

if [ "$COUNT" -eq 1 ]; then
  CHOSEN=0
else
  echo "Найдено несколько нод:"
  for i in "${!VALID_PORTS[@]}"; do
    echo "  $((i+1))) ${VALID_PORTS[$i]} — ${VALID_IDS[$i]} (${VALID_NAMES[$i]})"
  done
  while true; do
    echo -n "Выбери номер: "
    read -r CHOICE
    if [[ "$CHOICE" =~ ^[0-9]+$ ]] && [ "$CHOICE" -ge 1 ] && [ "$CHOICE" -le "$COUNT" ]; then
      CHOSEN=$((CHOICE-1))
      break
    fi
    echo "Неверный номер."
  done
fi

PORT="${VALID_PORTS[$CHOSEN]}"
NODE="${VALID_IDS[$CHOSEN]}"

sed -i "s|^SERIAL_PORT=.*|SERIAL_PORT=$PORT|" .env
sed -i "s|^NODE_ID=.*|NODE_ID=$NODE|" .env

echo "Записано в .env: SERIAL_PORT=$PORT, NODE_ID=$NODE"