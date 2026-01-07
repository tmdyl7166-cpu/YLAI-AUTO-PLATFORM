#!/usr/bin/env bash
set -e

# Auto run basic checks and append summary to README.

API_PORT=${API_PORT:-8001}
WEB_PORT=${WEB_PORT:-8080}
API_TARGET=${API_TARGET:-http://127.0.0.1:${API_PORT}}

root_dir=$(cd "$(dirname "$0")/.." && pwd)
cd "$root_dir"

ts() { date '+%F %T'; }

echo "[checks] API=${API_TARGET} WEB=http://127.0.0.1:${WEB_PORT}"

api_code=$(curl -s -o /dev/null -w '%{http_code}' "${API_TARGET}/health" || true)
web_code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${WEB_PORT}/health" || true)
page_code=$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${WEB_PORT}/pages/index.html" || true)

echo "API /health -> ${api_code}"
echo "WEB /health -> ${web_code}"
echo "WEB /pages/index.html -> ${page_code}"

echo "[checks] WS monitor probe"
API_TARGET="$API_TARGET" python3 scripts/probe_ws.py || true

echo "[checks] HX simulated validation"
HX_SIM_VALIDATE=1 python3 hx.py --dry-run || true

summary="\n### 自动检查报告 ($(ts))\n- API /health: ${api_code}\n- WEB /health: ${web_code}\n- WEB /pages/index.html: ${page_code}\n- 说明：如返回非 200，可能服务未启动或端口占用。\n\n运行命令：\n\n\`\`\`bash\nAPI_PORT=${API_PORT} WEB_PORT=${WEB_PORT} API_TARGET=${API_TARGET} ./start.sh containers\ndocker compose logs -f\n./start.sh probe-ws\nHX_SIM_VALIDATE=1 python3 hx.py --dry-run\n\`\`\`\n"

perl -0777 -pe "BEGIN{undef $/} s/\n## 🧭 Compose 统一入口与日志查看/\n${summary}\n## 🧭 Compose 统一入口与日志查看/s" -i README.md || {
  echo "[warn] perl patch failed; appending summary to end of README"
  printf "%s\n" "$summary" >> README.md
}

echo "[checks] summary appended to README.md"
