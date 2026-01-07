# SLO 与告警阈值说明

此文档提供平台常用 SLO（服务等级目标）示例，并给出如何调整 Prometheus 告警阈值的建议。

## 建议 SLO（示例）

- 可用性（Availability）: 99.9%（每月宕机时间 < 43.2 分钟）
- 响应时间（p95）: < 1s
- 错误率（5xx）: < 0.5%

## 调整告警阈值的建议

- 将 `HighResponseTime` 告警阈值与 SLO 对齐，例如若 SLO 为 p95 < 0.8s，则将告警阈值从 1s 降为 0.8s。
- 错误率告警应根据业务峰值与正常流量动态调整：建议先以 5% 作为紧急阈值，随后根据历史数据优化。

## 回滚与验证

1. 修改 `monitoring/prometheus-rules.yml` 中的 `expr` 或 `for` 字段。
2. 在测试环境先验证：将 Prometheus 指向测试实例并观察 24 小时报警触发情况。
3. 可通过 Grafana 面板查看 `http_request_duration_seconds` 的历史分布来决定合适阈值。

## 运行检查

- 在修改规则后，运行 `promtool check rules monitoring/prometheus-rules.yml` 来验证语法（需在本地安装 Prometheus 工具）。
