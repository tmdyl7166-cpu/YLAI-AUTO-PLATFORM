#!/bin/bash
# 多模型预安装脚本
# 联动部署四个本地AI模型，实现专用性功能分配

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查docker是否运行
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker未运行，请先启动Docker"
        exit 1
    fi
}

# 等待服务健康检查
wait_for_service() {
    local service_name=$1
    local max_attempts=30
    local attempt=1

    log_info "等待 $service_name 服务启动..."

    while [ $attempt -le $max_attempts ]; do
        if docker ps | grep -q "$service_name" && docker exec "$service_name" ollama list >/dev/null 2>&1; then
            log_success "$service_name 服务已就绪"
            return 0
        fi

        log_info "等待 $service_name... ($attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    log_error "$service_name 服务启动失败"
    return 1
}

# 拉取单个模型
pull_model() {
    local service_name=$1
    local model_name=$2
    local display_name=$3

    log_info "开始拉取 $display_name ($model_name)..."

    if docker exec "$service_name" ollama list | grep -q "$model_name"; then
        log_success "$display_name 已存在，跳过拉取"
        return 0
    fi

    log_info "拉取 $display_name 中..."
    if docker exec "$service_name" ollama pull "$model_name"; then
        log_success "$display_name 拉取成功"
        return 0
    else
        log_error "$display_name 拉取失败"
        return 1
    fi
}

# 主函数
main() {
    log_info "=== YLAI 多模型AI联动部署预安装脚本 ==="
    log_info "功能分配："
    log_info "  1. qwen3:8b     - 中文处理与内容理解"
    log_info "  2. llama3.1:8b  - 任务规划与指令理解"
    log_info "  3. deepseek-r1:8b - 复杂推理与决策制定"
    log_info "  4. gpt-oss:20b  - 创意生成与文本优化"
    echo

    check_docker

    # 启动所有Ollama服务
    log_info "启动所有Ollama服务..."
    docker compose -f docker-compose.multi.yml up -d ollama-qwen ollama-llama ollama-deepseek ollama-gptoss

    # 等待服务启动
    wait_for_service "ylai-ollama-qwen" || exit 1
    wait_for_service "ylai-ollama-llama" || exit 1
    wait_for_service "ylai-ollama-deepseek" || exit 1
    wait_for_service "ylai-ollama-gptoss" || exit 1

    echo
    log_info "开始拉取AI模型..."

    # 按顺序拉取模型（从小到大，便于监控进度）
    local pull_order=(
        "ylai-ollama-qwen:qwen3:8b:Qwen3 (中文处理)"
        "ylai-ollama-llama:llama3.1:8b:Llama3.1 (任务规划)"
        "ylai-ollama-deepseek:deepseek-r1:8b:DeepSeek-R1 (复杂推理)"
        "ylai-ollama-gptoss:gpt-oss:20b:GPT-OSS (创意生成)"
    )

    local failed_models=()

    for model_spec in "${pull_order[@]}"; do
        IFS=':' read -r service model display_name <<< "$model_spec"

        if pull_model "$service" "$model" "$display_name"; then
            log_success "$display_name 部署成功"
        else
            log_error "$display_name 部署失败"
            failed_models+=("$display_name")
        fi
        echo
    done

    # 检查结果
    if [ ${#failed_models[@]} -eq 0 ]; then
        log_success "=== 所有AI模型部署成功！ ==="
        echo
        log_info "模型功能联动说明："
        log_info "  📝 内容理解 → qwen3:8b (中文文档分析)"
        log_info "  🧠 任务规划 → llama3.1:8b (指令理解协调)"
        log_info "  🤔 复杂推理 → deepseek-r1:8b (策略决策优化)"
        log_info "  🎨 创意生成 → gpt-oss:20b (文本润色增强)"
        echo
        log_info "启动完整服务："
        log_info "  docker compose -f docker-compose.multi.yml up -d"
        echo
        log_info "访问地址："
        log_info "  前端界面: http://localhost:9000"
        log_info "  AI系统:   http://localhost:9001"
    else
        log_error "=== 部分模型部署失败 ==="
        log_error "失败的模型: ${failed_models[*]}"
        log_info "请检查网络连接和磁盘空间后重试"
        exit 1
    fi
}

# 参数处理
case "${1:-}" in
    "status")
        log_info "检查模型状态..."
        docker compose -f docker-compose.multi.yml ps
        echo
        log_info "Ollama服务状态:"
        for service in qwen llama deepseek gptoss; do
            echo -n "  $service: "
            if docker exec "ylai-ollama-$service" ollama list >/dev/null 2>&1; then
                echo "运行中"
            else
                echo "未运行"
            fi
        done
        ;;
    "clean")
        log_warning "清理所有AI模型数据..."
        docker compose -f docker-compose.multi.yml down -v
        log_success "清理完成"
        ;;
    *)
        main "$@"
        ;;
esac