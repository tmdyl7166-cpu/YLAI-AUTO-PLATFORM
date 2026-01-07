#!/usr/bin/env bash
# hx.sh — 最高权限审计与修复助手（结构/行为/API/运行时）
set -euo pipefail

API_BASE=${API_BASE:-http://127.0.0.1:8001}
FRONTEND_BASE=${FRONTEND_BASE:-http://127.0.0.1:8080}
REPORT_DIR=${REPORT_DIR:-logs}
REPORT_FILE=${REPORT_DIR}/hx-report.json
SUMMARY_FILE=${REPORT_DIR}/hx-summary.txt
CONSISTENCY=${CONSISTENCY:-0}

mkdir -p "${REPORT_DIR}"

echo "[hx] start at $(date +%F\ %T)" >&2

declare -A REPORT
REPORT[ts]=$(date +%s)
REPORT[api_base]="${API_BASE}"
REPORT[frontend_base]="${FRONTEND_BASE}"

json_escape() { python3 -c "import json,sys; print(json.dumps(sys.stdin.read()))"; }

probe_http() {
  local url=$1
  local code; code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
  echo "$code"
}

section_structure() {
  echo "[hx] scanning structure" >&2
  local tree
  tree=$(find . -maxdepth 3 -type d -printf '%p\n' | sed 's#^./##' | sort)
  REPORT[structure]=$tree
}

section_behavior() {
  echo "[hx] scanning static code rules" >&2
  local findings
  findings=$(grep -RIn --include='*.js' --include='*.py' -E 'eval\(|exec\(|subprocess\.Popen\(|shell=True' || true)
  REPORT[behavior]=$findings
}

section_api() {
  echo "[hx] comparing frontend/backend API" >&2
  local backend_ok frontend_ok
  backend_ok=$(probe_http "${API_BASE}/health")
  frontend_ok=$(probe_http "${FRONTEND_BASE}/health")
  local pages_codes
  pages_codes="$(for p in /pages/index.html /pages/api-doc.html /pages/monitor.html /pages/run.html /pages/visual_pipeline.html /pages/rbac.html; do c=$(probe_http "${FRONTEND_BASE}${p}"); echo "$c $p"; done)"
  REPORT[api_backend_health]=$backend_ok
  REPORT[api_frontend_health]=$frontend_ok
  REPORT[api_pages]="$pages_codes"

  # 401 接受策略端点
  local status_code modules_code
  status_code=$(probe_http "${API_BASE}/api/status")
  modules_code=$(probe_http "${API_BASE}/api/modules")
  REPORT[api_status_code]=$status_code
  REPORT[api_modules_code]=$modules_code
}

# 模块与权限规则检查
section_modules_policy() {
  echo "[hx] modules/policy checks" >&2
  local policy_file="modules_policy.json"
  if [ ! -f "$policy_file" ]; then
    REPORT[modules_policy]="missing"
    return
  fi
  local js_dir="frontend/static/js/modules"
  local css_dir="frontend/static/css/modules"
  local violations=""
  # 规则：仅允许 .js/.css
  if [ -d "$js_dir" ]; then
    while IFS= read -r f; do
      case "$f" in *.js) ;; *) violations+="bad_ext_js:$f\n" ;; esac
    done < <(find "$js_dir" -type f)
    # 禁止危险模式（eval/new Function）
    bad=$(grep -RIn -E 'eval\(|new Function\(' "$js_dir" || true)
    [ -n "$bad" ] && violations+="$bad\n"
  fi
  if [ -d "$css_dir" ]; then
    while IFS= read -r f; do
      case "$f" in *.css) ;; *) violations+="bad_ext_css:$f\n" ;; esac
    done < <(find "$css_dir" -type f)
  fi
  # HTML 禁止内联脚本/样式
  html_bad=$(grep -RIn --include='*.html' -E '<script(?![^>]*src=)|style="' frontend/pages || true)
  REPORT[modules_policy]="$(printf '%s' "$violations" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
  REPORT[html_policy]="$(printf '%s' "$html_bad" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
}

section_runtime() {
  echo "[hx] runtime traces" >&2
  local mod; mod=$(curl -s "${API_BASE}/api/modules" 2>/dev/null || true)
  local status; status=$(curl -s "${API_BASE}/api/status" 2>/dev/null || true)
  REPORT[runtime_modules]="$mod"
  REPORT[runtime_status]="$status"
}

write_report() {
  echo "[hx] writing ${REPORT_FILE}" >&2
  {
    echo '{'
    echo '  "ts":' "${REPORT[ts]}",
    echo '  "api_base":' "$(printf '%s' "${REPORT[api_base]}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')",
    echo '  "frontend_base":' "$(printf '%s' "${REPORT[frontend_base]}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')",
    echo '  "structure":' "$(printf '%s' "${REPORT[structure]:-}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')",
    echo '  "behavior":' "$(printf '%s' "${REPORT[behavior]:-}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')",
    echo '  "api": {'
    echo '    "backend_health":' "$(printf '%s' "${REPORT[api_backend_health]:-}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')",
    echo '    "frontend_health":' "$(printf '%s' "${REPORT[api_frontend_health]:-}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')",
    echo '    "pages":' "$(printf '%s' "${REPORT[api_pages]:-}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
    echo '    "status_code":' "$(printf '%s' "${REPORT[api_status_code]:-}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')",
    echo '    "modules_code":' "$(printf '%s' "${REPORT[api_modules_code]:-}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
    echo '  },'
    echo '  "runtime": {'
    echo '    "modules":' "$(printf '%s' "${REPORT[runtime_modules]:-}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')",
    echo '    "status":' "$(printf '%s' "${REPORT[runtime_status]:-}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')"
    echo '  }'
    echo '}'
  } > "${REPORT_FILE}"
}

write_summary() {
  echo "[hx] writing ${SUMMARY_FILE}" >&2
  local pass=0 total=0
  # 规则：health 必须 200；前端 pages 必须 200；status/modules 允许 401
  [ "${REPORT[api_backend_health]}" = "200" ] && pass=$((pass+1)); total=$((total+1))
  [ "${REPORT[api_frontend_health]}" = "200" ] && pass=$((pass+1)); total=$((total+1))
  # pages 统计
  while read -r line; do
    code=$(echo "$line" | awk '{print $1}');
    [ "$code" = "200" ] && pass=$((pass+1)); total=$((total+1))
  done <<< "${REPORT[api_pages]}"
  # 401 接受策略
  [[ "${REPORT[api_status_code]}" = "200" || "${REPORT[api_status_code]}" = "401" ]] && pass=$((pass+1)); total=$((total+1))
  [[ "${REPORT[api_modules_code]}" = "200" || "${REPORT[api_modules_code]}" = "401" ]] && pass=$((pass+1)); total=$((total+1))

  echo "pass ${pass}/${total}" > "${SUMMARY_FILE}"
}

# main
section_structure
section_behavior
section_api
section_modules_policy
section_runtime
write_report
write_summary

echo "[hx] done -> ${REPORT_FILE}" >&2
echo "[hx] summary -> ${SUMMARY_FILE}" >&2

# 可选：运行一致性校验（前端引用/脚本/配置路径）
if [[ "${CONSISTENCY}" == "1" ]]; then
  echo "[hx] consistency_check enabled" >&2
  if command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1; then
    PYBIN=$(command -v python3 || command -v python)
    "${PYBIN}" scripts/consistency_check.py || true
    if [[ -f "${REPORT_DIR}/consistency.txt" ]]; then
      echo "[hx] consistency -> ${REPORT_DIR}/consistency.txt" >&2
    fi
    if [[ -f "${REPORT_DIR}/consistency.json" ]]; then
      echo "[hx] consistency JSON -> ${REPORT_DIR}/consistency.json" >&2
    fi
  else
    echo "[hx] skip consistency_check: python not found" >&2
  fi
fi
