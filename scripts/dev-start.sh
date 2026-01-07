#!/bin/bash

set -e

echo "🚀 Starting YLAI Auto Platform Development Environment..."

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 检查并创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    python -m pip install --upgrade pip wheel setuptools
    if [ -f backend/requirements.txt ]; then
        echo "📦 Installing backend dependencies..."
        python -m pip install -r backend/requirements.txt
    fi
else
    source .venv/bin/activate
fi

# 启动后端 (后台运行)
echo "📦 Starting Backend on http://0.0.0.0:8001"
uvicorn backend.app:app --host 0.0.0.0 --port 8001 --reload --reload-delay 0.5 &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 检查前端依赖
cd "$PROJECT_ROOT/frontend"
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install --no-audit --no-fund
fi

# 启动前端
echo "🎨 Starting Frontend on http://0.0.0.0:3001"
CHOKIDAR_USEPOLLING=true CHOKIDAR_INTERVAL=10000 npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Services started:"
echo "   Backend:  http://0.0.0.0:8001"
echo "   Frontend: http://0.0.0.0:3001"
echo ""
echo "Press Ctrl+C to stop all services..."

# 捕获退出信号
trap "echo '🛑 Stopping services...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# 等待进程
wait
