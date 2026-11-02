#!/bin/bash

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi
KEEP_DAYS=${BACKUP_KEEP_DAYS:-7}

while true; do
  echo "Что архивировать?"
  echo "1. Всё"
  echo "2. Только jobs/"
  echo "3. Только subscriber-data/"
  echo "0. Отменить"
  read -p "Ваш выбор: " CHOICE
  case "$CHOICE" in
    1) DO_JOBS=true; DO_SUB=true; break ;;
    2) DO_JOBS=true; DO_SUB=false; break ;;
    3) DO_JOBS=false; DO_SUB=true; break ;;
    0) echo "Отменено."; exit 0 ;;
    *) echo "Ошибка: неверный выбор." ;;
  esac
done

if [ "$DO_JOBS" = true ]; then
  echo "Останавливаю mqtt-sender..."
  docker stop mqtt-sender >/dev/null 2>&1
fi
if [ "$DO_SUB" = true ]; then
  echo "Останавливаю mqtt-sub..."
  docker stop mqtt-sub >/dev/null 2>&1
fi

DATE=$(date +%Y-%m-%d)
CREATED=()

if [ "$DO_JOBS" = true ]; then
  tar -czf "backups/jobs-$DATE.tar.gz" jobs/ 2>/dev/null
  CREATED+=("backups/jobs-$DATE.tar.gz")
fi
if [ "$DO_SUB" = true ]; then
  tar -czf "backups/subscriber-data-$DATE.tar.gz" subscriber-data/ 2>/dev/null
  CREATED+=("backups/subscriber-data-$DATE.tar.gz")
fi

if [ "$DO_JOBS" = true ]; then
  echo "Запускаю mqtt-sender..."
  docker start mqtt-sender >/dev/null 2>&1
fi
if [ "$DO_SUB" = true ]; then
  echo "Запускаю mqtt-sub..."
  docker start mqtt-sub >/dev/null 2>&1
fi

find backups/ -name "*.tar.gz" -mtime +$KEEP_DAYS -delete

echo "Готово."
for f in "${CREATED[@]}"; do
  SIZE=$(du -h "$f" | cut -f1)
  echo "  Создан: $f ($SIZE)"
done
echo "Удалены архивы старше $KEEP_DAYS дней."