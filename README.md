# YLAI-AUTO-PLATFORM 🚀

> **统一架构 | 集中管理 | 规范运行 | AI驱动企业级爬虫平台**

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-green.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/Vue-3.4+-brightgreen.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.124+-blue.svg)](https://fastapi.tiangolo.com/)
[![AI](https://img.shields.io/badge/AI-Integrated-blueviolet.svg)](https://ollama.ai/)
[![Progress](https://img.shields.io/badge/Progress-95%25-brightgreen.svg)]()

## 📋 项目简介

YLAI-AUTO-PLATFORM 是一个基于统一内核架构的企业级自动化爬虫平台，采用前后端分离设计，深度集成本地AI模型，支持智能任务编排、分布式执行和实时监控。平台通过模块化插件系统实现功能扩展，具备完整的权限管理和安全防护机制。

### 🎯 核心特性

- **统一架构**: 基于FastAPI的后端 + Vue3前端，WebSocket实时通信
- **AI驱动**: 集成本地AI模型(qwen3:8b, llama3.1:8b, deepseek-r1:8b, gpt-oss:20b)，支持智能任务编排和自动化优化
- **智能反向工程**: AI增强的爬虫脚本，支持内容分析和数据提取
- **自动化任务执行**: AI代理系统，智能工作流管理和任务调度
- **预测性监控**: AI驱动的系统监控和异常预测分析
- **模块化**: 插件系统支持功能扩展，热加载机制
- **可视化**: DAG流水线编排，实时监控仪表板
- **安全可靠**: RBAC权限管理，API限流，审计日志
- **高性能**: 异步处理，缓存优化，性能监控

## 🚀 快速启动

### 环境要求




```bash
# 克隆项目
git clone <repository-url>

# 一键启动 (后端 + 前端)
./start.sh all

# 或分别启动
./start.sh api        # 启动后端 (端口8001)
./start.sh frontend   # 启动前端 (端口3001)
```

### Docker 部署

```bash
# 生产环境部署
docker compose -f docker/docker-compose.prod.yml up -d

# 开发环境部署
docker compose -f docker/docker-compose.dev.yml up -d
```

## 📖 功能说明

### 核心页面

基于 `frontend/pages/统一接口映射表.md` 的完整功能汇总：

#### 1. 主页面 (`index.html`)
- **功能**: 功能集合主页面，自然语言功能描述
- **接口**: `GET /api/modules` - 获取可用模块列表

#### 2. 任务执行 (`run.html`)
- **功能**: 任务中心，执行爬虫和自动化任务
- **接口**:
  - `POST /api/run` - 执行任务
  - `GET /api/tasks` - 获取任务列表
  - `WS /ws/pipeline/{task_id}` - 实时任务进度

#### 3. API文档 (`api-doc.html`)
- **功能**: 接口映射与进度展示
- **接口**: `GET /docs` - 自动生成的API文档

#### 4. 系统监控 (`monitor.html`)
- **功能**: 后端健康与服务追踪
- **接口**:
  - `GET /health` - 健康检查
  - `WS /ws/logs` - 实时日志
  - `GET /metrics` - 性能指标

#### 5. DAG流水线 (`visual_pipeline.html`)
- **功能**: 企业级DAG可视化流水线编排
- **接口**:
  - `POST /api/pipeline/run` - 执行流水线
  - `GET /api/pipeline/status` - 流水线状态

#### 6. 权限管理 (`rbac.html`)
- **功能**: 权限矩阵映射表
- **接口**: `node.rbac` - 权限管理相关接口

#### 7. AI演示 (`ai-demo.html`)
- **功能**: AI代理演示，自然语言转任务
- **接口**: `POST /api/generate` - AI推理

## 📊 项目状态

- **总体进度**: 95% ✅
- **基础架构**: 100% ✅ (脚本系统、映射同步、依赖库、性能优化全部完成)
- **核心功能**: 100% ✅ (风控识别、代理池、分布式采集全部完成)
- **高级功能**: 85% ✅ (AI集成完成83%，监控系统完成，脚本系统优化，前端模块完善)
- **AI集成**: 100% ✅ (4个AI模型集成，83.3%测试通过率，0.63集成评分)
- **文档同步**: 100% ✅ (所有文档已更新为最新状态)

## 🔧 开发指南

### 脚本开发规范

所有脚本必须放在 `backend/YLAI-AUTO-PLATFORM/scripts/` 下，支持多级目录自动加载：

```python
# backend/YLAI-AUTO-PLATFORM/scripts/spider/example_spider.py
from backend.core.base import BaseScript
from backend.core.registry import registry

@registry.register("example_spider")
class ExampleSpider(BaseScript):
    def run(self, **kwargs):
        # 实现业务逻辑
        pass
```

### 前端开发

```bash
cd frontend
npm install
npm run dev  # 开发模式
npm run build  # 生产构建
npm test      # 单元测试
npm run test:e2e  # E2E测试
```

### 插件开发

参考 `config/function_registry.json` 注册新插件：

```json
{
  "plugins": {
    "my_plugin": {
      "name": "我的插件",
      "path": "plugins/my_plugin",
      "enabled": true
    }
  }
}
```

## 🧪 测试与验证

### 自动化测试

```bash
# 后端测试
cd backend && python -m pytest

# 前端测试
cd frontend && npm test

# E2E测试
cd frontend && npm run test:e2e
```

### 健康检查

```bash
# 基础健康检查
curl http://localhost:8001/health

# 完整验证
./start.sh full-checks
```

## 📊 监控与运维

### 日志管理

- 后端日志: `backend/logs/`
- 系统日志: `logs/`
- 审计日志: 自动轮转，避免无限增长

### 性能监控

- 内置性能监控中间件
- 支持 Prometheus 指标导出
- 实时性能仪表板

### 备份恢复

```bash
# 自动备份
python YLAI-AUTO-PLATFORM/scripts/backup_manager.py

# 恢复备份
python YLAI-AUTO-PLATFORM/scripts/restore_manager.py <backup_file>
```

## 🔒 安全机制

### 权限管理
- RBAC 角色权限控制
- JWT Token 认证
- API 限流防护

### 数据安全
- 敏感信息加密存储
- 请求参数过滤
- XSS/CSRF 防护

### 网络安全
- HTTPS 强制跳转
- CORS 配置
- 防火墙规则

## 📚 文档

- [详细优化指南](docs/DETAILED_OPTIMIZATION_GUIDE.md)
- [实施计划](docs/IMPLEMENTATION_PLAN.md)
- [API文档](docs/API_FULL.md)
- [部署指南](docs/DEPLOY_GUIDE.md)

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

感谢所有贡献者和用户对本项目的支持！

---

**YLAI-AUTO-PLATFORM** - 让自动化更智能，让爬虫更专业！
