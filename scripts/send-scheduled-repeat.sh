#!/bin/bash
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
MSG=$(cat "$1")
docker exec -e MSG_TEXT="$MSG" mqtt-sender python3 /send.py