#!/bin/bash
echo "Введите текст сообщения:"
read -r MSG
docker exec -e MSG_TEXT="$MSG" mqtt-sender python3 /send.py