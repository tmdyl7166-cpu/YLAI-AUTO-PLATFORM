#!/usr/bin/env bash
# 从 monitoring/grafana/dashboards 自动导入 dashboard 到 Grafana
set -euo pipefail

GRAFANA_URL=${GRAFANA_URL:-http://localhost:3000}
GRAFANA_API_KEY=${GRAFANA_API_KEY:-}
DASH_DIR=monitoring/grafana/dashboards

if [ -z "$GRAFANA_API_KEY" ]; then
  echo "请设置环境变量 GRAFANA_API_KEY（可在 Grafana UI 中创建 API key）"
  exit 2
fi

for f in "$DASH_DIR"/*.json; do
  [ -e "$f" ] || continue
  echo "导入仪表盘: $f"
  payload=$(jq -c '{dashboard: . , overwrite: true}' "$f")
  curl -sS -X POST "$GRAFANA_URL/api/dashboards/db" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $GRAFANA_API_KEY" \
    -d "$payload" | jq .
done

echo "✓ 仪表盘导入完成"
