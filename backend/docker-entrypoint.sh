#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] running startup checks and database migrations"

# run startup checks if available
if [ -x "/app/docker/startup-check.sh" ]; then
  /app/docker/startup-check.sh || true
fi

# run alembic migrations if alembic is installed
if command -v alembic >/dev/null 2>&1; then
  echo "[entrypoint] running alembic upgrade head"
  alembic upgrade head || { echo "alembic upgrade failed" >&2; exit 1; }
else
  echo "[entrypoint] alembic not available, skipping migrations"
fi

exec "$@"
