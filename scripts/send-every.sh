#!/bin/bash
echo "Введите имя задания (например: daily):"
read -r NAME

echo "Введите интервал (30m, 2h, 1d):"
read -r INTERVAL

echo "Введите текст сообщения:"
read -r MSG

NUM=$(echo $INTERVAL | grep -oE '^[0-9]+')
UNIT=$(echo $INTERVAL | grep -oE '[a-z]+$')

case "$UNIT" in
  m|min) CRON="*/$NUM * * * *" ;;
  h|hour) CRON="0 */$NUM * * *" ;;
  d|day) CRON="0 0 */$NUM * *" ;;
  *) echo "Неверный формат. Используй 30m, 2h, 1d"; exit 1 ;;
esac

FILE="/tmp/scheduled-$NAME.txt"
echo "$MSG" > "$FILE"

TAG="meshtastic-local:$NAME"
LINE="$CRON LANG=C.UTF-8 LC_ALL=C.UTF-8 /bin/bash $(pwd)/scripts/send-scheduled-repeat.sh $FILE # $TAG"

(crontab -l 2>/dev/null | grep -v "# $TAG\$"; echo "$LINE") | crontab -
echo "Задание '$NAME' каждые $INTERVAL"