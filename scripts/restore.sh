#!/bin/bash

while true; do
  echo "Что восстановить?"
  echo "1. jobs/"
  echo "2. subscriber-data/"
  echo "0. Отменить"
  read -p "Ваш выбор: " CHOICE
  case "$CHOICE" in
    1) TARGET="jobs"; PREFIX="jobs"; CONTAINER="mqtt-sender"; break ;;
    2) TARGET="subscriber-data"; PREFIX="subscriber-data"; CONTAINER="mqtt-sub"; break ;;
    0) echo "Отменено."; exit 0 ;;
    *) echo "Ошибка: неверный выбор." ;;
  esac
done

ARCHIVES=($(ls -1 backups/${PREFIX}-*.tar.gz 2>/dev/null | sort -r))

if [ ${#ARCHIVES[@]} -eq 0 ]; then
  echo "Архивов этого типа нет."
  exit 0
fi

while true; do
  echo "Доступные архивы $TARGET:"
  for i in "${!ARCHIVES[@]}"; do
    FILENAME=$(basename "${ARCHIVES[$i]}")
    DATESTR=${FILENAME#${PREFIX}-}
    DATESTR=${DATESTR%.tar.gz}
    echo "$((i+1)). $DATESTR"
  done
  echo "0. Отменить"
  
  read -p "За какой период? (Введи номер или дату ГГГГ-ММ-ДД): " PERIOD

  if [ "$PERIOD" = "0" ]; then
    echo "Отменено."
    exit 0
  fi

  SELECTED=""
  if [[ "$PERIOD" =~ ^[0-9]+$ ]] && [ "$PERIOD" -ge 1 ] && [ "$PERIOD" -le "${#ARCHIVES[@]}" ]; then
    SELECTED="${ARCHIVES[$((PERIOD-1))]}"
  else
    MATCH=$(ls -1 "backups/${PREFIX}-${PERIOD}.tar.gz" 2>/dev/null)
    if [ -n "$MATCH" ]; then
      SELECTED="$MATCH"
    fi
  fi

  if [ -n "$SELECTED" ]; then
    break
  else
    echo "Ошибка: неверный выбор."
  fi
done

echo "Останавливаю $CONTAINER..."
docker stop $CONTAINER >/dev/null 2>&1

echo "Распаковываю $(basename "$SELECTED")..."
tar -xzf "$SELECTED" -C .

echo "Запускаю $CONTAINER..."
docker start $CONTAINER >/dev/null 2>&1

FILES_COUNT=$(find "$TARGET" -type f | wc -l)
echo "Восстановлено: $(basename "$SELECTED") (файлов: $FILES_COUNT)."