#!/bin/sh
set -eu

MM="http://localhost:3001"
TOKEN_FILE="/secrets/mm_token"
JAR=$(mktemp)

mkdir -p /secrets

until curl -sf http://localhost:3001/api/health > /dev/null; do
  sleep 1
done
sleep 3

if [ ! -s "$TOKEN_FILE" ]; then
  CSRF=$(curl -sf -c "$JAR" -b "$JAR" "$MM/api/csrf-token" | jq -r .csrfToken)
  curl -sf -c "$JAR" -b "$JAR" -H "X-CSRF-Token: $CSRF" -H 'Content-Type: application/json' \
    -d '{"username":"admin","password":"changeme"}' "$MM/api/auth/login" >/dev/null
  curl -sf -c "$JAR" -b "$JAR" -H "X-CSRF-Token: $CSRF" -X POST \
    "$MM/api/token/generate" | jq -r .token > "$TOKEN_FILE"
fi

AUTH="Authorization: Bearer $(cat "$TOKEN_FILE")"

SRC=""
while [ -z "$SRC" ]; do
  SRC=$(curl -sf -H "$AUTH" "$MM/api/sources" \
    | jq -c '.[] | select(.type=="meshtastic_tcp" and .name=="Default")' || true)
  sleep 1
done

ID=$(echo "$SRC" | jq -r .id)

PORT="${SERIAL_BRIDGE_PORT:-4403}"

echo "$SRC" \
  | jq --arg host "localhost" --argjson port "$PORT" '{config: {host: $host, port: $port, virtualNode: ((.config.virtualNode // {}) + {enabled: true, port: 4404, allowAdminCommands: false})}}' \
  | curl -sf -X PUT -H "$AUTH" -H 'Content-Type: application/json' -d @- "$MM/api/sources/$ID"

echo "Настройки отправлены. Ожидание открытия порта 4404..."
# Ждем, пока порт 4404 реально начнет принимать подключения
while ! nc -z localhost 4404; do
  sleep 1
done
echo "Порт 4404 открыт! Virtual Node готова."