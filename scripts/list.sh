#!/bin/bash

if [ ! -d "jobs" ] || [ -z "$(ls -A jobs/*.json 2>/dev/null)" ]; then
  echo "Активных заданий нет."
  exit 0
fi

echo "Активные задания:"

for f in jobs/*.json; do
  NAME=$(basename "$f" .json)
  
  # Если установлен jq, выводим красиво, иначе показываем как есть
  if command -v jq >/dev/null 2>&1; then
    TYPE=$(jq -r '.type' "$f")
    TEXT=$(jq -r '.text' "$f")
    
    if [ "$TYPE" = "once" ]; then
      SCHED=$(jq -r '.run_date' "$f")
    else
      VAL=$(jq -r '.interval_value' "$f")
      ITYPE=$(jq -r '.interval_type' "$f")
      RUNS=$(jq -r '.runs // 0' "$f")
      MAX=$(jq -r '.max_runs // 0' "$f")
      if [ "$MAX" = "0" ]; then
        SCHED="каждые $VAL $ITYPE (выполнено: $RUNS, бесконечно)"
      else
        SCHED="каждые $VAL $ITYPE (выполнено: $RUNS из $MAX)"
      fi
    fi
    echo "  [$NAME] ($TYPE, $SCHED) -> $TEXT"
  else
    echo "  [$NAME]:"
    cat "$f" | sed 's/^/    /'
  fi
done