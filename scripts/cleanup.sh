#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOGS_DIR="$ROOT_DIR/logs"
VENVDIR="$ROOT_DIR/.venv"

info() { echo "[INFO] $*"; }
warn() { echo "[WARN] $*"; }

info "Project root: $ROOT_DIR"

# 1) Docker safe prune (keeps in-use resources)
info "Pruning Docker unused resources..."
if command -v docker >/dev/null 2>&1; then
  docker system prune -f || warn "docker system prune failed"
  docker image prune -a -f || warn "docker image prune failed"
  docker volume prune -f || warn "docker volume prune failed"
  docker network prune -f || warn "docker network prune failed"
  if command -v docker >/dev/null 2>&1 && docker buildx ls >/dev/null 2>&1; then
    docker buildx prune -af || warn "docker buildx prune failed"
  fi
else
  warn "Docker not found, skip docker prune"
fi

# 2) Remove known heavy devcontainer images (if not in use)
DEV_IMAGES=(
  vsc-frontend-000d02e7e1fe14e0e04d33fa7263efe3ffbc6fefd43df1c06090fab3842725df-features-uid
  vsc-frontend-000d02e7e1fe14e0e04d33fa7263efe3ffbc6fefd43df1c06090fab3842725df-features
  vsc-ylai-auto-platform-96c62585044f5450f54dc886f3b6a96735dc2847d84270453f5ed2ad23ea37b7-features-uid
  vsc-ylai-auto-platform-96c62585044f5450f54dc886f3b6a96735dc2847d84270453f5ed2ad23ea37b7-features
  vsc--ee51c6f7e41df1a9043517c6018acef2d6055f76bf152ae91072f3b6ff74b020-uid
  vsc-ylai-auto-platform-96c62585044f5450f54dc886f3b6a96735dc2847d84270453f5ed2ad23ea37b7-uid
)
if command -v docker >/dev/null 2>&1; then
  for img in "${DEV_IMAGES[@]}"; do
    if docker images | awk '{print $1}' | grep -qx "$img"; then
      info "Removing dev image: $img"
      docker rmi "$img" || warn "Failed to remove $img"
    fi
  done
fi

# 3) Python caches: mypy cache and pip cache
info "Cleaning Python caches..."
rm -rf "$ROOT_DIR/.mypy_cache" || true
if [ -x "$VENVDIR/bin/python" ]; then
  "$VENVDIR/bin/python" -m pip cache purge || warn "pip cache purge failed"
else
  warn "Python venv not found, skip pip cache purge"
fi

# 4) npm cache
info "Cleaning npm cache..."
npm cache clean --force || warn "npm cache clean failed"

# 5) Logs: archive then clear current reports
info "Archiving logs..."
mkdir -p "$LOGS_DIR/archive"
for f in "$LOGS_DIR"/*.json "$LOGS_DIR"/*.txt; do
  [ -e "$f" ] && mv "$f" "$LOGS_DIR/archive/" || true
done

# 6) Optional: reset front-end route status (comment out to keep)
STATUS_JSON="$FRONTEND_DIR/pages/data/module-status.json"
ROUTES_JSON="$FRONTEND_DIR/pages/data/module-routes-status.json"
if [ -f "$STATUS_JSON" ]; then
  info "Resetting module-status.json to empty object"
  echo "{}" > "$STATUS_JSON"
fi
if [ -f "$ROUTES_JSON" ]; then
  info "Resetting module-routes-status.json to empty object"
  echo "{}" > "$ROUTES_JSON"
fi

# 7) Apt caches (optional; requires sudo)
if command -v sudo >/dev/null 2>&1; then
  info "Cleaning apt caches (sudo) ..."
  sudo apt-get clean || true
  sudo apt-get autoclean || true
  sudo apt-get autoremove -y || true
fi

info "Cleanup completed. Current Docker disk usage:"
if command -v docker >/dev/null 2>&1; then
  docker system df || true
fi
