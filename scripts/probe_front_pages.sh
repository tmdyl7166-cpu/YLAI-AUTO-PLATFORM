#!/usr/bin/env bash
set -euo pipefail
BASE="${BASE_URL:-http://127.0.0.1:3000}"
PAGES=(index api-doc api-map run ai-demo login visual_pipeline monitor rbac)
echo "[probe] BASE=$BASE"
# wait health up to 20s
for i in $(seq 1 20); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$BASE/health" || true)
  echo "health:$code"
  [[ "$code" == "200" ]] && break
  sleep 1
done
# summarize and fail if health not 200
if [[ "$code" != "200" ]]; then
  echo "error: frontend health check failed (code=$code)" >&2
  exit 1
fi
UA="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari"
FAIL=0
for p in "${PAGES[@]}"; do
  url="$BASE/pages/$p"
  tmp=$(mktemp)
  code=$(curl -L -sS -H "User-Agent: $UA" -o "$tmp" -w '%{http_code}' "$url" || true)
  marker="/static/js/pages/${p//-/_}.js"
  hasScript=$(grep -c "$marker" "$tmp" || true)
  leftPlaceholder=$(grep -c "__ASSET_VERSION__" "$tmp" || true)
  echo "$code $url script_marker:$marker present:$hasScript placeholder_left:$leftPlaceholder"
  if [[ "$code" != "200" || "$hasScript" -eq 0 || "$leftPlaceholder" -gt 0 ]]; then
    FAIL=1
  fi
  rm -f "$tmp"
done
if [[ "$FAIL" -ne 0 ]]; then
  echo "error: front pages check failed" >&2
  exit 2
fi
echo "ok: front pages check passed"
