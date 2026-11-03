#!/bin/bash

echo "Проверка требований:"
FAIL=0

if command -v meshtastic >/dev/null 2>&1; then
  echo -e "  [\033[32m OK \033[0m] meshtastic CLI"
else
  echo -e "  [\033[31mFAIL\033[0m] meshtastic CLI (Установите по инструкции из README)"
  FAIL=1
fi

if id -nG | grep -qw "dialout"; then
  echo -e "  [\033[32m OK \033[0m] Группа dialout"
else
  echo -e "  [\033[31mFAIL\033[0m] Группа dialout (Установите по инструкции из README)"
  FAIL=1
fi

if [ $FAIL -ne 0 ]; then
  echo -e "\nИсправьте ошибки и запустите снова."
  exit 1
fi