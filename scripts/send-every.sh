#!/bin/bash

while true; do
  echo "Введите имя задания (например: weather):"
  read -r NAME
  if [[ "$NAME" =~ ^[a-zA-Z0-9_-]+$ ]]; then break; else echo "Ошибка: только английские буквы, цифры, - и _."; fi
done

while true; do
  echo "Выберите интервал:"
  echo "1. Минуты"
  echo "2. Часы"
  echo "3. Дни"
  echo -n "Ваш выбор: "
  read -r TYPE
  if [[ "$TYPE" =~ ^[123]$ ]]; then break; else echo "Ошибка: введите 1, 2 или 3."; fi
done

while true; do
  echo -n "Введите интервал (например: 2): "
  read -r NUM
  if [[ "$NUM" =~ ^[1-9][0-9]*$ ]]; then break; else echo "Ошибка: введите целое число больше нуля."; fi
done

while true; do
  echo -n "Введите время первого запуска (ЧЧ:ММ): "
  read -r TIME
  if [[ "$TIME" =~ ^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$ ]]; then break; else echo "Ошибка: неверный формат времени."; fi
done

echo "Сколько раз выполнить? (Enter - бесконечно, или введите число, например: 4):"
read -r COUNT
if [ -n "$COUNT" ]; then
  if ! [[ "$COUNT" =~ ^[1-9][0-9]*$ ]]; then
    echo "Ошибка: неверное число. Будет выполнено бесконечно."
    COUNT="0"
  fi
else
  COUNT="0"
fi

while true; do
  echo "Введите текст сообщения:"
  read -r MSG
  if [ -n "$MSG" ]; then break; else echo "Ошибка: текст не может быть пустым."; fi
done

START_DT="$(date +%Y-%m-%d) $TIME:00"

case "$TYPE" in
  1) ITYPE="minutes" ;;
  2) ITYPE="hours" ;;
  3) ITYPE="days" ;;
esac

cat > "jobs/$NAME.json" <<EOF
{
  "name": "$NAME",
  "text": "$MSG",
  "type": "interval",
  "interval_type": "$ITYPE",
  "interval_value": $NUM,
  "start_date": "$START_DT",
  "max_runs": $COUNT,
  "runs": 0
}
EOF

if [ "$COUNT" = "0" ]; then
  echo "Задание '$NAME' создано: каждые $NUM $ITYPE, начиная с $START_DT, бесконечно."
else
  echo "Задание '$NAME' создано: каждые $NUM $ITYPE, начиная с $START_DT, всего $COUNT раз."
fi