#!/usr/bin/env bash
set -euo pipefail

# 将误存到桌面根目录的配置/数据文件，归位到项目 `YLAI-AUTO-PLATFORM/` 下。
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DESKTOP_ROOT="$HOME/桌面"

echo "Project root: $PROJECT_ROOT"
echo "Desktop root: $DESKTOP_ROOT"

declare -A MOVE_MAP=(
  ["$DESKTOP_ROOT/.env.dev"]="$PROJECT_ROOT/.env.dev"
  ["$DESKTOP_ROOT/.space_check.tmp"]="$PROJECT_ROOT/logs/.space_check.tmp"
  ["$DESKTOP_ROOT/function_registry.json"]="$PROJECT_ROOT/frontend/function_registry.json"
  ["$DESKTOP_ROOT/modules_policy.json"]="$PROJECT_ROOT/frontend/modules_policy.json"
  ["$DESKTOP_ROOT/核心指向.json"]="$PROJECT_ROOT/docs/核心指向.json"
)

mkdir -p "$PROJECT_ROOT/logs" "$PROJECT_ROOT/frontend" "$PROJECT_ROOT/docs"

for src in "${!MOVE_MAP[@]}"; do
  dst="${MOVE_MAP[$src]}"
  if [[ -e "$src" ]]; then
    echo "Relocating: $src -> $dst"
    mkdir -p "$(dirname "$dst")"
    mv -f "$src" "$dst"
  else
    echo "Skip missing: $src"
  fi
done

echo "Done. Verify with: ls -la $PROJECT_ROOT && ls -la $PROJECT_ROOT/frontend && ls -la $PROJECT_ROOT/docs"