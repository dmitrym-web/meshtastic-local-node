#!/bin/bash
echo "Введите дату и время (today 14:30 или tomorrow 09:00):"
read -r WHEN

echo "Введите текст сообщения:"
read -r MSG

DAY=$(echo $WHEN | cut -d' ' -f1)
AT=$(echo $WHEN | cut -d' ' -f2)

HOUR=$(echo $AT | cut -d: -f1)
MIN=$(echo $AT | cut -d: -f2)

FILE="/tmp/scheduled-msg-$(date +%s).txt"
echo "$MSG" > "$FILE"

if [ "$DAY" = "tomorrow" ]; then
  TARGET_DATE=$(date -d "tomorrow" +%d)
  TARGET_MONTH=$(date -d "tomorrow" +%m)
  LINE="$MIN $HOUR $TARGET_DATE $TARGET_MONTH * LANG=C.UTF-8 LC_ALL=C.UTF-8 /bin/bash $(pwd)/scripts/send-scheduled-once.sh $FILE # meshtastic-local:at"
else
  LINE="$MIN $HOUR * * * LANG=C.UTF-8 LC_ALL=C.UTF-8 /bin/bash $(pwd)/scripts/send-scheduled-once.sh $FILE # meshtastic-local:at"
fi

(crontab -l 2>/dev/null | grep -v "# meshtastic-local:at\$"; echo "$LINE") | crontab -
echo "Запланировано на $WHEN"