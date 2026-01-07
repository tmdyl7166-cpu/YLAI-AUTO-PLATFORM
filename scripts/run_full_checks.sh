#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
BASE_URL=${BASE_URL:-http://127.0.0.1:8001}
UA=${UA:-"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari"}
LOG_DIR="$ROOT_DIR/logs"
mkdir -p "$LOG_DIR"

echo "[run] base=$BASE_URL"

echo "[run] probe /health"
if ! BASE_URL="$BASE_URL" bash "$ROOT_DIR/scripts/probe_health.sh"; then
  echo "[run] health probe failed" >&2
  exit 2
fi

echo "[run] checks:apis"
CHECK_TIMEOUT=${CHECK_TIMEOUT:-3.0} BASE_URL="$BASE_URL" python3 "$ROOT_DIR/scripts/checks_apis_accept401.py" | tee "$LOG_DIR/apis_check.json"

echo "[run] probe /metrics (optional)"
curl -sS "$BASE_URL/metrics" | head -n 5 | tee "$LOG_DIR/metrics_head.txt" >/dev/null || true

echo "[run] validate pages (static)"
if ! python3 "$ROOT_DIR/scripts/validate_pages.py" | tee "$LOG_DIR/pages_validate.json"; then
  echo "[run] page validation failed" >&2
  exit 3
fi

echo "[run] repair suggestions (dry-run)"
APPLY=0 python3 "$ROOT_DIR/scripts/repair_pages.py" | tee "$LOG_DIR/pages_repair_suggestions.json" || true

echo "[run] checks:pages-strict"
pages=(/pages/index.html /pages/api-doc.html /pages/run.html /pages/monitor.html /pages/visual_pipeline.html)
extless=(/pages/index /pages/api-doc /pages/run /pages/monitor /pages/visual_pipeline)
FAIL=0
{
  for p in "${pages[@]}"; do
    code=$(curl -sS -L -H "User-Agent: $UA" -o /dev/null -w "%{http_code}" "$BASE_URL$p" || true)
    echo "$code $p"
    if [ "$code" != "200" ]; then FAIL=1; fi
  done
  for p in "${extless[@]}"; do
    code=$(curl -sS -L -H "User-Agent: $UA" -o /dev/null -w "%{http_code}" "$BASE_URL$p" || true)
    echo "$code $p"
    if [ "$code" != "200" ]; then FAIL=1; fi
  done
} | tee "$LOG_DIR/pages_check.txt"

if [ "$FAIL" != "0" ]; then
  echo "[run] page strict checks failed" >&2
  exit 3
fi

echo "[run] all checks passed"

echo "[run] ws probe"
if [ "${WS_STRICT:-0}" = "1" ]; then
  API_TARGET="$BASE_URL" WS_EXPECT_ACK=1 python3 "$ROOT_DIR/scripts/probe_ws.py" | tee "$LOG_DIR/ws_probe.txt"
else
  API_TARGET="$BASE_URL" python3 "$ROOT_DIR/scripts/probe_ws.py" | tee "$LOG_DIR/ws_probe.txt" || true
fi

# E2E DAG sample run (assert success)
echo "[run] e2e DAG sample"
if ! BASE_URL="$BASE_URL" python3 "$ROOT_DIR/scripts/e2e_dag_sample.py" | tee "$LOG_DIR/e2e_dag.txt"; then
  echo "[run] e2e DAG sample failed" >&2
  exit 4
fi

exit 0
