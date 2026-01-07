#!/bin/bash
# YLAI-AUTO-PLATFORM 快速优化脚本
# 用法: ./scripts/quick_optimize.sh [选项]

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."

    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi

    # 检查 Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js 未安装"
        exit 1
    fi

    # 检查 Redis (可选)
    if command -v redis-server &> /dev/null; then
        log_info "Redis 已安装"
    else
        log_warn "Redis 未安装，缓存功能将受限"
    fi
}

# 优化后端
optimize_backend() {
    log_info "优化后端配置..."

    # 创建必要的目录
    mkdir -p "$BACKEND_DIR/logs"
    mkdir -p "$BACKEND_DIR/backups"

    # 设置日志轮转
    cat > "$BACKEND_DIR/logging.conf" << EOF
[loggers]
keys=root

[handlers]
keys=consoleHandler,fileHandler

[formatters]
keys=simpleFormatter

[logger_root]
level=INFO
handlers=consoleHandler,fileHandler

[handler_consoleHandler]
class=StreamHandler
level=INFO
formatter=simpleFormatter
args=(sys.stdout,)

[handler_fileHandler]
class=handlers.RotatingFileHandler
level=INFO
formatter=simpleFormatter
args=('logs/app.log', 'a', 10485760, 5)

[formatter_simpleFormatter]
format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
datefmt=%Y-%m-%d %H:%M:%S
EOF

    # 创建环境变量模板
    cat > "$BACKEND_DIR/.env.example" << EOF
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost/ylai_platform

# Redis 配置
REDIS_URL=redis://localhost:6379

# JWT 配置
JWT_SECRET=your-secret-key-here
JWT_EXPIRE_MINUTES=30

# AI 配置
OLLAMA_URL=http://localhost:11434

# 监控配置
SENTRY_DSN=your-sentry-dsn-here

# 应用配置
DEBUG=false
WORKERS=4
EOF

    log_info "后端优化完成"
}

# 优化前端
optimize_frontend() {
    log_info "优化前端配置..."

    # 创建环境变量
    cat > "$FRONTEND_DIR/.env" << EOF
VITE_API_BASE_URL=http://localhost:8001
VITE_WS_URL=ws://localhost:8001
VITE_APP_ENV=development
EOF

    cat > "$FRONTEND_DIR/.env.production" << EOF
VITE_API_BASE_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com
VITE_APP_ENV=production
EOF

    # 更新 package.json 脚本
    cd "$FRONTEND_DIR"

    # 添加优化脚本
    npm pkg set scripts.lint="eslint src --ext .js,.vue"
    npm pkg set scripts.format="prettier --write src/**/*.{js,vue}"
    npm pkg set scripts.analyze="npm run build -- --mode analyze"

    cd "$PROJECT_ROOT"

    log_info "前端优化完成"
}

# 优化 Docker 配置
optimize_docker() {
    log_info "优化 Docker 配置..."

    # 创建多阶段构建的 Dockerfile
    cat > "$PROJECT_ROOT/docker/Dockerfile.optimized" << EOF
# 多阶段构建 - 后端
FROM python:3.11-slim as backend-builder

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 前端构建阶段
FROM node:18-alpine as frontend-builder

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ .
RUN npm run build

# 生产镜像
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \\
    nginx \\
    redis-server \\
    && rm -rf /var/lib/apt/lists/*

# 复制后端
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY backend/ /app/backend/

# 复制前端构建产物
COPY --from=frontend-builder /app/dist /var/www/html

# 配置 nginx
COPY docker/nginx.conf /etc/nginx/nginx.conf

# 设置工作目录
WORKDIR /app

# 暴露端口
EXPOSE 80 8001

# 启动脚本
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]
EOF

    log_info "Docker 优化完成"
}

# 创建监控配置
setup_monitoring() {
    log_info "设置监控配置..."

    # Prometheus 配置
    mkdir -p "$PROJECT_ROOT/monitoring"
    cat > "$PROJECT_ROOT/monitoring/prometheus.yml" << EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'ylai-backend'
    static_configs:
      - targets: ['localhost:8001']

  - job_name: 'ylai-frontend'
    static_configs:
      - targets: ['localhost:3001']
EOF

    # Grafana 仪表板配置
    cat > "$PROJECT_ROOT/monitoring/dashboard.json" << EOF
{
  "dashboard": {
    "title": "YLAI Platform Dashboard",
    "tags": ["ylai"],
    "timezone": "browser",
    "panels": [
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
EOF

    log_info "监控配置完成"
}

# 主函数
main() {
    echo "YLAI-AUTO-PLATFORM 快速优化工具"
    echo "================================="

    case "${1:-all}" in
        "check")
            check_dependencies
            ;;
        "backend")
            optimize_backend
            ;;
        "frontend")
            optimize_frontend
            ;;
        "docker")
            optimize_docker
            ;;
        "monitoring")
            setup_monitoring
            ;;
        "all")
            check_dependencies
            optimize_backend
            optimize_frontend
            optimize_docker
            setup_monitoring
            log_info "所有优化完成！"
            ;;
        *)
            echo "用法: $0 [check|backend|frontend|docker|monitoring|all]"
            exit 1
            ;;
    esac
}

main "$@"