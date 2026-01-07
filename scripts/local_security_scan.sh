#!/usr/bin/env bash
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
OUT_DIR="$ROOT/logs/security"
mkdir -p "$OUT_DIR"

mode=${1:-all}

has() { command -v "$1" >/dev/null 2>&1; }

echo "[scan] mode=$mode"

if [ "$mode" = "sbom" ] || [ "$mode" = "all" ]; then
  if has syft; then
    echo "[sbom] generating SBOM (spdx-json)"
    syft packages dir:"$ROOT" -o spdx-json > "$OUT_DIR/sbom.spdx.json" || true
    echo "[sbom] output: $OUT_DIR/sbom.spdx.json"
  else
    echo "[sbom] syft not found. Install: curl -sSfL https://raw.githubusercontent.com/anchore/syft/main/install.sh | sh"
  fi
fi

if [ "$mode" = "trivy" ] || [ "$mode" = "all" ]; then
  if has trivy; then
    echo "[trivy] scanning filesystem (high,critical)"
    trivy fs --exit-code 1 --severity HIGH,CRITICAL --skip-dirs .venv --no-progress --format table "$ROOT" | tee "$OUT_DIR/trivy-fs.txt" || true
    echo "[trivy] scanning configs (IaC)"
    trivy config --exit-code 0 --severity HIGH,CRITICAL --no-progress --format table "$ROOT" | tee "$OUT_DIR/trivy-config.txt" || true
    echo "[trivy] outputs: $OUT_DIR/trivy-fs.txt, $OUT_DIR/trivy-config.txt"
  else
    echo "[trivy] not found. Install: https://aquasecurity.github.io/trivy/v0.54/getting-started/installation/"
  fi
fi

echo "[scan] done"
