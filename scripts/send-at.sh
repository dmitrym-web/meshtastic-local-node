#!/bin/bash

while true; do
  echo "Введите имя задания (например: meeting):"
  read -r NAME
  if [[ "$NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then break; else echo "Ошибка: только английские буквы, цифры, - и _."; fi
done

while true; do
  echo "Выберите дату:"
  echo "1. Сегодня"
  echo "2. Завтра"
  echo "3. Другая дата и время"
  echo -n "Ваш выбор: "
  read -r DATE_CHOICE
  if [[ "$DATE_CHOICE" =~ ^[123]$ ]]; then break; else echo "Ошибка: введите 1, 2 или 3."; fi
done

while true; do
  case "$DATE_CHOICE" in
    1)
      echo -n "Введите время (ЧЧ:ММ): "
      read -r TIME
      TARGET_DT="$(date +%Y-%m-%d) $TIME:00"
      ;;
    2)
      echo -n "Введите время (ЧЧ:ММ): "
      read -r TIME
      TARGET_DT="$(date -d "tomorrow" +%Y-%m-%d) $TIME:00"
      ;;
    3)
      echo -n "Введите дату и время (ГГГГ-ММ-ДД ЧЧ:ММ): "
      read -r TARGET_DT
      TARGET_DT="$TARGET_DT:00"
      ;;
  esac

  if ! date -d "$TARGET_DT" >/dev/null 2>&1; then
    echo "Ошибка: неверный формат даты или времени."
    continue
  fi

  TARGET_TS=$(date -d "$TARGET_DT" +%s)
  NOW_TS=$(date +%s)
  if [ "$TARGET_TS" -le "$NOW_TS" ]; then
    echo "Ошибка: это время уже прошло. Введите будущее время."
    continue
  fi
  break
done

while true; do
  echo "Введите текст сообщения:"
  read -r MSG
  if [ -n "$MSG" ]; then break; else echo "Ошибка: текст не может быть пустым."; fi
done

cat > "jobs/$NAME.json" <<EOF
{
  "name": "$NAME",
  "text": "$MSG",
  "type": "once",
  "run_date": "$TARGET_DT"
}
EOF

echo "Задание '$NAME' запланировано на $TARGET_DT"