#!/usr/bin/env bash
set -euo pipefail

# 项目根目录
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

echo "[one-click] working dir: $ROOT_DIR"

# Python 虚拟环境
if [[ ! -d .venv ]]; then
  echo "[one-click] creating venv .venv"
  python3 -m venv .venv
fi
source .venv/bin/activate
echo "[one-click] venv activated: $(which python)"

# 安装依赖（与 VS Code 任务保持一致）
# 允许在 Python 3.14 下使用稳定 ABI 构建 pydantic-core，避免构建失败
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1
python -m pip install -U pip wheel setuptools || true
# 确保必要运行依赖存在
python -m pip install -U uvicorn fastapi || true
# 跳过根 requirements 以避免与后端依赖冲突（如 pydantic-core 构建）
if [[ -f backend/requirements.txt ]]; then
  echo "[one-click] installing backend/requirements.txt"
  python -m pip install -r backend/requirements.txt || true
fi

# 启动后端（以包名导入，适配 backend.* 路径）
# 确保顶层包（如 core/ 与 backend/）可被导入
export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"
RELOAD_FLAG=${RELOAD:-}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-8001}

LOG_FILE=${ONECLICK_LOG:-/tmp/oneclick.log}
echo "[one-click] starting uvicorn backend.app:app on ${HOST}:${PORT} reload=${RELOAD_FLAG:-} | logs -> ${LOG_FILE}"

# 选择 uvicorn 可执行；否则使用 python -m uvicorn
if command -v uvicorn >/dev/null 2>&1; then
  START_CMD=(uvicorn backend.app:app --host "${HOST}" --port "${PORT}")
else
  START_CMD=(python -m uvicorn backend.app:app --host "${HOST}" --port "${PORT}")
fi

if [[ -n "${RELOAD_FLAG}" ]]; then
  START_CMD+=(--reload --reload-dir backend --reload-dir frontend)
fi

# 将输出写入日志文件并同时打印到控制台
{
  echo "[one-click] cmd: ${START_CMD[*]}"
  "${START_CMD[@]}"
} 2>&1 | tee "${LOG_FILE}"
