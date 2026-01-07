#!/usr/bin/env bash
# 验证 Prometheus 规则与配置的脚本
set -euo pipefail

PROMTOOL=${PROMTOOL:-promtool}
RULES_FILE=monitoring/prometheus-rules.yml
PROM_CFG=monitoring/prometheus.yml

if ! command -v "$PROMTOOL" >/dev/null 2>&1; then
  echo "promtool 未安装，请安装 Prometheus 工具集（promtool）。"
  echo "在 Debian/Ubuntu 上： sudo apt-get install prometheus" || true
  exit 2
fi

echo "检查 Prometheus 规则文件: $RULES_FILE"
$PROMTOOL check rules "$RULES_FILE"

echo "检查 Prometheus 主配置: $PROM_CFG"
$PROMTOOL check config "$PROM_CFG"

echo "✓ Prometheus 配置与规则校验通过"
