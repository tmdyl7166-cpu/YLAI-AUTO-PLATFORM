#!/bin/bash

# YLAI-AUTO-PLATFORM 生产启动检查脚本
# 验证环境完整性、依赖可用性，启动前进行全面检查

set -e

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║                  YLAI-AUTO-PLATFORM 生产启动前检查                         ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查计数
CHECKS_PASSED=0
CHECKS_FAILED=0

# 日志函数
log_check() {
    local name=$1
    local result=$2
    if [ "$result" -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $name"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $name"
        ((CHECKS_FAILED++))
    fi
}

# ==================== 1. 环境变量检查 ====================
echo && echo "1️⃣ 环境变量检查..."

[ -f ".env" ] || [ -f ".env.production" ]
log_check "环境配置文件存在" $?

# 检查关键环境变量
for var in SECRET_KEY DATABASE_URL REDIS_URL API_PORT; do
    if grep -q "^$var=" .env* 2>/dev/null; then
        log_check "环境变量 $var 已配置" 0
    else
        log_check "环境变量 $var 已配置" 1
    fi
done

# ==================== 2. 依赖检查 ====================
echo && echo "2️⃣ Python 依赖检查..."

python -m pip list | grep -q "fastapi"
log_check "FastAPI 已安装" $?

python -m pip list | grep -q "uvicorn"
log_check "uvicorn 已安装" $?

python -m pip list | grep -q "sqlalchemy"
log_check "SQLAlchemy 已安装" $?

python -m pip list | grep -q "redis"
log_check "redis 已安装" $?

# ==================== 3. 数据库检查 ====================
echo && echo "3️⃣ 数据库连接检查..."

if command -v psql &> /dev/null; then
    # PostgreSQL 连接测试
    psql --version > /dev/null 2>&1
    log_check "PostgreSQL 客户端可用" $?
else
    log_check "PostgreSQL 客户端可用" 1
fi

# 检查数据库迁移脚本
if [ -d "alembic/versions" ]; then
    log_check "数据库迁移脚本存在" 0
else
    log_check "数据库迁移脚本存在" 1
fi

# ==================== 4. Redis 检查 ====================
echo && echo "4️⃣ Redis 连接检查..."

if command -v redis-cli &> /dev/null; then
    redis-cli ping > /dev/null 2>&1
    log_check "Redis 服务可达" $?
else
    log_check "Redis 客户端可用" 1
fi

# ==================== 5. 目录和权限检查 ====================
echo && echo "5️⃣ 目录和权限检查..."

for dir in data logs backups; do
    if [ -d "$dir" ] && [ -w "$dir" ]; then
        log_check "目录 $dir 可写入" 0
    else
        mkdir -p "$dir"
        log_check "目录 $dir 已创建" $?
    fi
done

# ==================== 6. SSL/TLS 证书检查 ====================
echo && echo "6️⃣ SSL/TLS 证书检查..."

if [ -f "certs/server.crt" ] && [ -f "certs/server.key" ]; then
    log_check "SSL 证书已配置" 0
else
    if [ "$ENV" = "production" ]; then
        log_check "SSL 证书已配置" 1
    else
        echo -e "${YELLOW}⚠${NC} SSL 证书未配置（开发环境可选）"
    fi
fi

# ==================== 7. 日志配置检查 ====================
echo && echo "7️⃣ 日志配置检查..."

if grep -q "logging" backend/app.py 2>/dev/null; then
    log_check "日志系统已配置" 0
else
    log_check "日志系统已配置" 1
fi

# ==================== 8. API 文档检查 ====================
echo && echo "8️⃣ API 文档检查..."

if grep -q "/docs" backend/app.py 2>/dev/null; then
    log_check "API 文档已启用" 0
else
    log_check "API 文档已启用" 1
fi

# ==================== 9. 健康检查端点检查 ====================
echo && echo "9️⃣ 健康检查端点检查..."

if grep -q "@app.get.*health" backend/app.py 2>/dev/null; then
    log_check "健康检查端点已定义" 0
else
    log_check "健康检查端点已定义" 1
fi

# ==================== 10. 监控和指标检查 ====================
echo && echo "🔟 监控和指标检查..."

if grep -q "prometheus" backend/requirements.txt 2>/dev/null; then
    log_check "Prometheus 已配置" 0
else
    log_check "Prometheus 已配置" 1
fi

# ==================== 结果总结 ====================
echo && echo "╔════════════════════════════════════════════════════════════════════════════╗"

TOTAL=$((CHECKS_PASSED + CHECKS_FAILED))
PERCENTAGE=$((CHECKS_PASSED * 100 / TOTAL))

echo "║  检查完成："
echo "║    ✓ 通过: $CHECKS_PASSED"
echo "║    ✗ 失败: $CHECKS_FAILED"
echo "║    📊 通过率: $PERCENTAGE%"
echo "╚════════════════════════════════════════════════════════════════════════════╝"

# 启动应用
if [ $CHECKS_FAILED -eq 0 ]; then
    echo && echo "✅ 所有检查通过，启动应用..."
    if [ -f "alembic/env.py" ]; then
        echo "🔄 执行数据库迁移..."
        alembic upgrade head
    fi
    echo "🚀 启动 Uvicorn 服务..."
    exec uvicorn backend.app:app --host 0.0.0.0 --port ${API_PORT:-8001} --workers ${API_WORKERS:-4}
else
    echo && echo "❌ 部分检查失败，请检查上述错误后重试"
    exit 1
fi
