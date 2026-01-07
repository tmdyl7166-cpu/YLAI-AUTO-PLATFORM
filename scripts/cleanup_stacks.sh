#!/usr/bin/env bash
set -euo pipefail

# Cleanup only project-specific stacks and residual containers/networks
PROJECTS=(ylai-dev ylai-prod)
ROOT_DIR="$(cd "$(dirname "$0")"/.. && pwd)"
cd "$ROOT_DIR"

echo "[cleanup] starting targeted cleanup for: ${PROJECTS[*]}"
for P in "${PROJECTS[@]}"; do
  echo "[cleanup] project: $P"
  # Attempt compose down for both dev/prod compose files
  docker compose -p "$P" -f docker/docker-compose.dev.yml down 2>/dev/null || true
  docker compose -p "$P" -f docker/docker-compose.prod.yml down 2>/dev/null || true

  # Remove containers with matching project label
  mapfile -t cids < <(docker ps -a -q --filter "label=com.docker.compose.project=$P")
  for cid in "${cids[@]}"; do
    echo "[cleanup] removing container $cid"
    docker rm -f "$cid" || true
  done

  # Remove networks created by this project
  mapfile -t nets < <(docker network ls --format '{{.Name}}' | grep "^${P}_" || true)
  for net in "${nets[@]}"; do
    echo "[cleanup] removing network $net"
    docker network rm "$net" || true
  done

  # Optional: remove named volumes associated to the stacks (safe subset)
  # Uncomment if you want to drop stack-specific volumes
  # mapfile -t vols < <(docker volume ls --format '{{.Name}}' | grep "^${P}_" || true)
  # for vol in "${vols[@]}"; do
  #   echo "[cleanup] removing volume $vol"
  #   docker volume rm "$vol" || true
  # done
done

echo "[cleanup] done"
