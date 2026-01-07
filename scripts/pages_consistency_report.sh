#!/usr/bin/env bash
set -e

STRICT_LOG=${STRICT_LOG:-logs/pages_strict.txt}
SMOKE_LOG=${SMOKE_LOG:-logs/pages_smoke.txt}
REPORT=${REPORT:-logs/pages_consistency_report.txt}

pages=(/pages/index.html /pages/api-doc.html /pages/run.html /pages/monitor.html /pages/visual_pipeline.html)

summ() {
  echo "== Pages Consistency Report =="
  date '+Generated at: %Y-%m-%d %H:%M:%S'
  echo "Strict source: $STRICT_LOG"
  echo "Smoke source : $SMOKE_LOG"
  echo
}

collect_codes() {
  echo "-- HTTP Status Codes --"
  for p in "${pages[@]}"; do
    s=$(grep -E "[0-9]{3} ${p}$" "$SMOKE_LOG" | tail -n1 | awk '{print $1}')
    echo "${p}: ${s:-N/A}"
  done
  echo
}

suggest() {
  echo "-- Suggestions --"
  for p in "${pages[@]}"; do
    s=$(grep -E "[0-9]{3} ${p}$" "$SMOKE_LOG" | tail -n1 | awk '{print $1}')
    if [ "$s" != "200" ]; then
      case "$p" in
        /pages/run.html)
          echo "$p: 检查是否存在 /static/css/run.css 与路由挂载，以及页面入口 /static/js/pages/run.js 可达。";;
        /pages/index.html)
          echo "$p: 校验标题 'Index 子站' 与文案 '夜灵多功能检测仪' 已更新；检查静态资源服务是否正常。";;
        /pages/visual_pipeline.html)
          echo "$p: 校验 id=tasksList 占位已存在；检查 /static/js/pages/visual_pipeline.js 加载与路由映射。";;
        *)
          echo "$p: 检查静态路径、Nginx/后端静态挂载与 200 返回条件。";;
      esac
    fi
  done
  echo
}

mkdir -p logs
{
  summ
  collect_codes
  suggest
} > "$REPORT"

echo "Report generated: $REPORT"
