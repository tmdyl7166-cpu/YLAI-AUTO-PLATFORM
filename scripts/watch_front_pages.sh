#!/usr/bin/env bash
set -euo pipefail
BASE_URL="${BASE_URL:-http://127.0.0.1:3000}"
INTERVAL="${INTERVAL_SEC:-60}"
LOG_FILE="${LOG_FILE:-logs/front_pages_checks.log}"
mkdir -p "$(dirname "$LOG_FILE")"
echo "[watch] base=$BASE_URL interval=${INTERVAL}s log=$LOG_FILE"
while true; do
  echo "=== $(date '+%F %T') ===" | tee -a "$LOG_FILE"
  if bash "$(dirname "$0")/probe_front_pages.sh" BASE_URL="$BASE_URL" 2>&1 | tee -a "$LOG_FILE"; then
    echo "[watch] ok" | tee -a "$LOG_FILE"
  else
    echo "[watch] failed" | tee -a "$LOG_FILE"
  fi
  sleep "$INTERVAL"
done
