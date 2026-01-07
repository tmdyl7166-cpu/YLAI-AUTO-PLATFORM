#!/usr/bin/env bash
set -euo pipefail
BASE_URL=${BASE_URL:-http://127.0.0.1:8001}
MAX_WAIT=${MAX_WAIT:-30}
for i in $(seq 1 "$MAX_WAIT"); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/health" || true)
  echo "$code"
  if [ "$code" = "200" ]; then
    exit 0
  fi
  sleep 1
done
echo "health check failed after ${MAX_WAIT}s"
exit 2