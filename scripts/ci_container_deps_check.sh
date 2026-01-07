#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
LOG_DIR="$ROOT_DIR/logs"
MATRIX_JSON="$LOG_DIR/container_deps_matrix.json"
DOC_MD="$ROOT_DIR/docs/CONTAINER_DEPS.md"

mkdir -p "$LOG_DIR"

echo "[ci] scanning container dependencies..."
python "$ROOT_DIR/scripts/scan_container_deps.py" > "$MATRIX_JSON"

echo "[ci] generating markdown summary..."
python "$ROOT_DIR/scripts/gen_container_deps_md.py" >/dev/null || true

echo "[ci] checking version conflicts..."
python - "$MATRIX_JSON" <<'PY'
import sys, json
path = sys.argv[1]
data = json.loads(open(path, 'r', encoding='utf-8').read())
conf = data.get('conflicts') or {}
if conf:
    print('[ci][fail] version conflicts detected:')
    for name, vers in sorted(conf.items()):
        print(f" - {name}: {', '.join(vers)}")
    sys.exit(2)
print('[ci][ok] no version conflicts found')
PY

echo "[ci] matrix: $MATRIX_JSON"
echo "[ci] doc:    $DOC_MD"
