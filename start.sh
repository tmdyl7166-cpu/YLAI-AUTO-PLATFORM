#!/usr/bin/env bash
set -e

API_PORT=${API_PORT:-8001}
FRONTEND_PORT=${FRONTEND_PORT:-8080}
API_TARGET=${API_TARGET:-http://127.0.0.1:${API_PORT}}

usage() {
  cat <<EOF
Usage: ./start.sh [mode]

Modes:
  api         Start FastAPI (backend.app:app) on ${API_PORT}
  simple      Start simplified API (backend.main:app) on ${API_PORT}
  frontend    Start frontend server on ${FRONTEND_PORT} (proxy -> ${API_TARGET})
  all         Start api (background) + frontend
  auto        Auto-start full stack with browser (auto-start.sh functionality)
  test-auth   Run authentication tests (test_auth.sh functionality)
  docker-up   docker compose -f docker/docker-compose.yml up -d
  docker-down docker compose -f docker/docker-compose.yml down
  up-api      Start only API container (docker)
  up-web      Start only Web container (docker)
  up-ai       Start only AI container (docker)
  down-api    Stop only API container (docker)
  down-web    Stop only Web container (docker)
  down-ai     Stop only AI container (docker)
  ai-up       docker compose -f docker/docker-compose.yml up -d ai
  ai-down     docker compose -f docker/docker-compose.yml down ai
  checks-dev  Probe backend & pages via curl (dev)
  checks-prod Probe backend & web (compose)
  open        Open unified entry index.html in default browser
  docker-all  Alias: docker-up (start api+web+ai services)
  help        Show this help text
  build       Build api/web images (docker)
  build-ai    Build ai-app image (docker)
  up-all      Build (if needed) and compose up api+web+ai
  containers  Start all containers (api+web+ai) via compose
  containers-down Stop all containers (api+web+ai) via compose
  install-deps Install Node.js and Python venv (best-effort)
  dev-frontend  Frontend dev mode (hot reload, Node required)
  prod-frontend Frontend prod via docker compose
  dev-backend   Backend dev mode (uvicorn --reload)
  prod-backend  Backend prod via docker compose
  dev-ai        AI app dev (local run if available)
  prod-ai       AI app prod via docker compose
  full-checks   Run health+API+pages strict checks
  sbom          Generate SBOM (if syft available)
  sec-scan      Run local Trivy scans (if trivy available)
  repair-pages  Dry-run repair suggestions for frontend pages (APPLY=1 to modify)
  safe-api      Start API with recovery on failure
  safe-frontend Start frontend with recovery on failure
  safe-all      Start api+frontend with recovery (probe health)
