#!/bin/bash
echo "Введите имя задания для удаления:"
read -r NAME

if [ -f "jobs/$NAME.json" ]; then
  rm -f "jobs/$NAME.json"
  echo "Задание '$NAME' удалено"
else
  echo "Задание '$NAME' не найдено"
fi