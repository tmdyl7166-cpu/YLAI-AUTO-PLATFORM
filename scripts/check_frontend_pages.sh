#!/bin/bash

# 网页检查脚本
# 检查所有页面是否能正常访问和渲染

set -e

BASE_URL="http://localhost:3001"
TIMEOUT=10

echo "=========================================="
echo "页面完整性和功能检查"
echo "=========================================="
echo ""

# 页面列表
declare -a PAGES=(
    "/"
    "/run"
    "/monitor"
    "/api-doc"
    "/visual-pipeline"
    "/rbac"
    "/settings"
    "/about"
    "/login"
    "/history"
    "/stats"
)

# 检查结果
PASSED=0
FAILED=0
ERRORS=()

# 检查每个页面
for page in "${PAGES[@]}"; do
    echo -n "检查页面: $page ... "
    
    # 发送请求并检查响应
    http_code=$(curl -s -o /tmp/page.html -w "%{http_code}" --connect-timeout 5 --max-time $TIMEOUT "$BASE_URL$page" || echo "000")
    
    if [ "$http_code" = "200" ]; then
        # 检查是否是有效的 HTML
        if grep -q "<!DOCTYPE html>" /tmp/page.html || grep -q "<html" /tmp/page.html; then
            echo "✓ 通过 (HTTP $http_code)"
            ((PASSED++))
        else
            echo "✗ 失败 - 无效的 HTML"
            ((FAILED++))
            ERRORS+=("$page: 响应不是有效的 HTML")
        fi
    else
        echo "✗ 失败 (HTTP $http_code)"
        ((FAILED++))
        ERRORS+=("$page: HTTP $http_code")
    fi
done

# 输出统计结果
echo ""
echo "=========================================="
echo "检查结果统计"
echo "=========================================="
echo "通过: $PASSED"
echo "失败: $FAILED"
echo ""

if [ ${#ERRORS[@]} -gt 0 ]; then
    echo "错误详情:"
    for error in "${ERRORS[@]}"; do
        echo "  - $error"
    done
    exit 1
else
    echo "✓ 所有页面检查通过!"
    exit 0
fi
