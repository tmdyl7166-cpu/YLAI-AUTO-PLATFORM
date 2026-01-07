#!/bin/bash
set -e

# 自动安装 Python 3.10+
echo "[Python] 安装..."
sudo apt update
sudo apt install -y python3.10 python3.10-venv python3.10-dev || true

# 自动安装 Node.js 20 LTS（nvm）
echo "[Node.js] 安装..."
if ! command -v nvm >/dev/null 2>&1; then
  curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
  export NVM_DIR="$HOME/.nvm"
  source "$NVM_DIR/nvm.sh"
fi
nvm install 20
nvm use 20

# 自动安装 .NET 8 LTS
echo "[.NET] 安装..."
wget https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install -y dotnet-sdk-8.0 || true

# 自动安装 FastAPI（虚拟环境）
echo "[FastAPI] 安装..."
python3.10 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install fastapi uvicorn watchdog

echo "[Frontend 注入] 处理占位符与资源版本..."
ASSET_VERSION=${ASSET_VERSION:-dev}
python3 YLAI-AUTO-PLATFORM/scripts/inject_assets.py || true

# 自动安装 Docker 最新
echo "[Docker] 安装..."
curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker
sudo usermod -aG docker $USER

echo "\n✅ 自动安装完成，请重启终端或执行 newgrp docker 以生效 Docker 用户组。"
