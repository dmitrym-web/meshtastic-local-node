#!/bin/bash
echo "Введите имя задания для удаления:"
read -r NAME

TAG="meshtastic-local:$NAME"
crontab -l 2>/dev/null | grep -v "# $TAG\$" | crontab -
rm -f "/tmp/scheduled-$NAME.txt"
echo "Задание '$NAME' удалено"