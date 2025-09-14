#!/usr/bin/env sh
set -eu

: "${ZAP_LOG_LEVEL:=INFO}"
: "${ZAP_STARTUP_TIMEOUT:=120}"
READY_URL="http://localhost:8080/JSON/core/view/version"

echo "[entrypoint] Cleanup stale locks & broken addons (safe)"
rm -f /home/zap/.ZAP/*.lck /home/zap/.ZAP/*.lock /home/zap/.ZAP/.ZAP.lock 2>/dev/null || true
rm -f /home/zap/.ZAP/plugin/*.zap* 2>/dev/null || true

echo "[entrypoint] Starting ZAP (no API key, bind 0.0.0.0:8080)"
/zap/zap.sh \
  -daemon \
  -host 0.0.0.0 \
  -port 8080 \
  -config api.disablekey=true \
  -config api.addrs.addr.name=.* \
  -config api.addrs.addr.regex=true \
  -config logger.level="${ZAP_LOG_LEVEL}" &

echo "[entrypoint] Waiting for ZAP to be ready (timeout: ${ZAP_STARTUP_TIMEOUT}s)"
end=$(( $(date +%s) + ZAP_STARTUP_TIMEOUT ))
while :; do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$READY_URL" || true)
  [ "$code" = "200" ] || [ "$code" = "403" ] && break
  [ "$(date +%s)" -ge "$end" ] && { echo >&2 "[entrypoint] ZAP failed to start within timeout"; exit 1; }
  sleep 2
done
echo "[entrypoint] ZAP is up."

echo "[entrypoint] Starting app: $*"
exec "$@"
