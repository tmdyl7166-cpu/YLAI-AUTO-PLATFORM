#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$ROOT_DIR/docker"

STACK_NAME="ylai-ai-dev"
COMPOSE_FILE="docker-compose.ai-dev.yml"

echo "[ai-dev] starting standalone AI dev container"
if ! docker compose -p "$STACK_NAME" -f "$COMPOSE_FILE" up -d --build; then
  echo "[ai-dev] compose up failed; targeted cleanup"
  cid=$(docker compose -p "$STACK_NAME" -f "$COMPOSE_FILE" ps -q ai-dev || true)
  if [ -n "${cid:-}" ]; then
    status=$(docker inspect -f '{{.State.Status}}' "$cid" 2>/dev/null || echo unknown)
    health=$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{end}}' "$cid" 2>/dev/null || echo none)
    echo "[ai-dev] removing failed ai-dev $cid status=$status health=$health"
    docker rm -f "$cid" || true
  fi
  echo "[ai-dev] retry"
  docker compose -p "$STACK_NAME" -f "$COMPOSE_FILE" up -d --build
fi

echo "[ai-dev] tail logs (Ctrl-C to stop)"
docker compose -p "$STACK_NAME" -f "$COMPOSE_FILE" logs -f ai-dev
