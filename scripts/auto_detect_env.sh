#!/usr/bin/env bash
set -euo pipefail

# Auto-detect free ports and primary IP, optionally update .env, and cleanup caches
# Usage:
#   bash scripts/auto_detect_env.sh                 # print detected values
#   APPLY=1 bash scripts/auto_detect_env.sh         # write to .env (create or patch)
#   CLEAN=1 bash scripts/auto_detect_env.sh         # cleanup caches (logs, __pycache__, tmp)
#   PRUNE=1 bash scripts/auto_detect_env.sh         # docker prune (dangling) & stop orphans

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
ENV_FILE="$ROOT_DIR/.env"

info() { echo "[auto] $*"; }
warn() { echo "[auto] WARN: $*" >&2; }
# Optional cleanup routines
cleanup_caches() {
  info "Cleanup caches and temp files"
  local root="$ROOT_DIR"
  # logs: keep last snapshot if present
  mkdir -p "$root/logs"
  find "$root/logs" -type f -name "*.log" -delete || true
  find "$root" -type d -name "__pycache__" -exec rm -rf {} + || true
  # tmp
  rm -rf "$root/.tmp" || true
  mkdir -p "$root/.tmp"
}

docker_prune() {
  if command -v docker >/dev/null 2>&1; then
    info "Docker prune (dangling) and stop orphans"
    docker system prune -f || true
    docker network prune -f || true
    docker volume prune -f || true
  else
    warn "docker command not found, skip prune"
  fi
}


is_port_free() {
  local port=$1
  (echo >/dev/tcp/127.0.0.1/$port) >/dev/null 2>&1 && return 1 || return 0
}

find_free_port() {
  local start=$1
  local end=${2:-$((start+100))}
  local p
  for p in $(seq "$start" "$end"); do
    if is_port_free "$p"; then echo "$p"; return 0; fi
  done
  return 1
}

detect_ip() {
  # Prefer IPv4 on primary interface; fallback to 127.0.0.1
  local ip
  ip=$(hostname -I 2>/dev/null | awk '{print $1}') || true
  if [[ -z "${ip:-}" ]]; then ip="127.0.0.1"; fi
  echo "$ip"
}

# Defaults
DEF_API=${BASE_API_PORT:-8001}
DEF_WEB=${BASE_WEB_PORT:-8080}
DEF_AI=${BASE_AI_PORT:-9001}

API_PORT=$(find_free_port "$DEF_API" $((DEF_API+200)) || echo "$DEF_API")
WEB_PORT=$(find_free_port "$DEF_WEB" $((DEF_WEB+200)) || echo "$DEF_WEB")
AI_PORT=$(find_free_port "$DEF_AI" $((DEF_AI+200)) || echo "$DEF_AI")
IP_ADDR=$(detect_ip)

API_BASE="http://${IP_ADDR}:${API_PORT}"
WEB_BASE="http://${IP_ADDR}:${WEB_PORT}"
AI_BASE="http://${IP_ADDR}:${AI_PORT}"

info "Detected IP      : $IP_ADDR"
info "API port/base    : $API_PORT | $API_BASE"
info "WEB port/base    : $WEB_PORT | $WEB_BASE"
info "AI port/base     : $AI_PORT | $AI_BASE"

emit_env() {
  cat <<EOF
BASE_URL=${API_BASE}
PORT=${WEB_PORT}
OLLAMA_URL=${AI_BASE}
API_TARGET=http://api:${API_PORT}
EOF
}

if [[ "${APPLY:-0}" == "1" ]]; then
  info "Writing detected values to .env"
  # Create or patch .env (preserve other keys)
  tmp=$(mktemp)
  touch "$ENV_FILE"
  # Remove keys we manage, then append fresh values
  grep -Ev '^(BASE_URL|PORT|OLLAMA_URL|API_TARGET)=' "$ENV_FILE" > "$tmp" || true
  emit_env >> "$tmp"
  mv "$tmp" "$ENV_FILE"
  info "Updated: $ENV_FILE"
else
  info "To apply, run: APPLY=1 bash scripts/auto_detect_env.sh"
  emit_env
fi

# Perform optional cleanup
if [[ "${CLEAN:-0}" == "1" ]]; then
  cleanup_caches || true
fi
if [[ "${PRUNE:-0}" == "1" ]]; then
  docker_prune || true
fi

exit 0
