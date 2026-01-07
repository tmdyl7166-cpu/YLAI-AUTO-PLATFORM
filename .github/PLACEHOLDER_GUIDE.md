# gitc.md 占位字段填写指南

**文档用途**: 帮助用户快速理解和填写 `gitc.md` 中的占位预留字段  
**更新日期**: 2025-12-13  
**适用版本**: gitc.md v2.0.0

---

## 📋 快速导航

1. [必填字段](#必填字段) - 必须填写的核心配置
2. [可选字段](#可选字段) - 可选的扩展配置
3. [填写示例](#填写示例) - 不同项目类型的示例
4. [验证方法](#验证方法) - 如何验证配置正确性

---

## 必填字段

### 1. external_rules_file（外部规则文件）

**位置**: `gitc.md` → 📌 外部规则配置指向

**说明**: 指定外部 JSON 规则文件路径（可选配置）

**填写规则**:
- ✅ **留空推荐**: `"external_rules_file": ""` - 使用 gitc.md + 内置规则
- ✅ **指定外部**: `"external_rules_file": "YL-project-rules.json"` - 必须满足：
  - 文件与 `.github/` 同级（项目根目录）
  - 文件名以 `YL` 或 `yl` 开头
  - 有效的 JSON 格式

**示例**:
```json
// 方式1：使用默认规则（推荐）
{
  "external_rules_file": ""
}

// 方式2：使用外部规则文件
{
  "external_rules_file": "YL-backend-rules.json"
}
```

---

### 2. 项目基本信息

**位置**: `gitc.md` → 1. 项目概览 → 项目基本信息

**说明**: 描述项目的基本情况，帮助 Copilot 理解项目上下文

**必填项**:
- **项目名称**: 项目的中文或英文名称
- **项目类型**: Web应用 / 微服务 / 数据处理 / 桌面应用等
- **主要用途**: 项目的核心功能和业务价值

**填写模板**:
```markdown
**项目名称**: 电商订单管理系统  
**项目类型**: Web应用（前后端分离）  
**主要用途**: 提供订单创建、支付、物流跟踪等完整的电商订单生命周期管理
```

---

### 3. 技术栈与架构

**位置**: `gitc.md` → 1. 项目概览 → 技术栈与架构

**说明**: 列出项目使用的主要技术和架构

**必填项**:
- **主要语言**: 编程语言及版本
- **框架/库**: 主要框架和依赖库
- **数据库**: 使用的数据库系统
- **部署环境**: 运行环境和容器化方案
- **CI/CD**: 持续集成和部署工具

**填写模板**:
```markdown
- **主要语言**: Python 3.11
- **框架/库**: Django 4.2, Django REST Framework 3.14
- **数据库**: PostgreSQL 15, Redis 7
- **部署环境**: Docker Compose, AWS ECS
- **CI/CD**: GitHub Actions
```

---

### 4. 核心模块说明

**位置**: `gitc.md` → 1. 项目概览 → 核心模块说明

**说明**: 列出项目的核心模块及其职责

**必填项**: 至少列出 3-5 个核心模块

**填写模板**:
```markdown
- **模块1**: 用户认证模块 - 负责用户注册、登录、JWT令牌管理
- **模块2**: 订单管理模块 - 处理订单创建、修改、取消、状态流转
- **模块3**: 支付网关模块 - 集成支付宝、微信支付等第三方支付
- **模块4**: 库存管理模块 - 实时库存查询、锁定、释放
- **模块5**: 通知中心模块 - 邮件、短信、站内信等多渠道通知
```

---

## 可选字段

### 1. 自定义语言规范

**位置**: `gitc.md` → 4. 语言约定与编码规范 → 自定义覆盖规则

**说明**: 覆盖默认的语言编码规范（留空使用默认）

**示例**:
```markdown
- **Python**: 
  - 命名: snake_case（保持默认）
  - 缩进: 2空格（覆盖默认的4空格）
  - 文档: NumPy风格（覆盖默认的Google风格）
  
- **JavaScript**:
  - 引号: 单引号（覆盖默认的双引号）
  - 分号: 必须（保持默认）
```

---

### 2. 自定义路径规则

**位置**: `gitc.md` → 5. 路径包含与排除策略 → 自定义路径规则

**说明**: 覆盖默认的路径包含/排除策略（留空使用默认）

**示例**:
```json
{
  "include": [
    "backend/**",
    "frontend/src/**",
    "shared/utils/**"
  ],
  "exclude": [
    "**/*.test.js",
    "backend/migrations/**",
    "frontend/public/**"
  ]
}
```

---

### 3. 自定义优化重点

**位置**: `gitc.md` → 6. 优化重点与质量目标 → 自定义优化重点

**说明**: 指定项目特别关注的优化方向（留空应用所有默认维度）

**示例**:
```markdown
- **优先级1**: 性能优化 - 重点关注数据库查询优化和缓存策略
- **优先级2**: 安全加固 - 强化API认证和输入验证
- **优先级3**: 代码复用 - 抽取公共业务逻辑到工具模块
```

---

### 4. 自定义CI/CD配置

**位置**: `gitc.md` → 7. CI/CD 集成配置 → 自定义校验配置

**说明**: 指定自定义的 schema 或校验脚本（留空使用默认）

**示例**:
```markdown
- **自定义 schema**: config/project-schema.json
- **额外校验脚本**: scripts/lint-all.sh
- **校验触发条件**: 仅在 main 和 develop 分支触发
```

---

### 5. 自定义钩子函数

**位置**: `gitc.md` → 8. 自定义钩子与扩展 → 钩子配置

**说明**: 配置扫描前/优化后执行的脚本（留空不使用）

**示例**:
```json
{
  "onBeforeScan": "scripts/pre-scan-check.sh",
  "onAfterOptimize": "scripts/post-optimize-test.sh"
}
```

---

## 填写示例

### 示例 1: Python Django Web 项目

```markdown
### 项目基本信息（必填字段）
**项目名称**: 企业内部管理系统  
**项目类型**: Web应用（单体架构）  
**主要用途**: 提供员工管理、考勤打卡、报销审批等企业内部管理功能

### 技术栈与架构（必填字段）
- **主要语言**: Python 3.11
- **框架/库**: Django 4.2, Celery 5.3
- **数据库**: PostgreSQL 15, Redis 7
- **部署环境**: Docker, Nginx, Gunicorn
- **CI/CD**: GitLab CI

### 核心模块说明（必填字段）
- **模块1**: 用户权限模块 - RBAC权限控制，支持多租户
- **模块2**: 考勤管理模块 - 打卡记录、请假审批、加班统计
- **模块3**: 报销审批模块 - 多级审批流程、费用类型配置
- **模块4**: 通知中心 - 邮件、企业微信消息推送
```

---

### 示例 2: React + Node.js 全栈项目

```markdown
### 项目基本信息（必填字段）
**项目名称**: 在线协作文档平台  
**项目类型**: 全栈Web应用（前后端分离 + 微服务）  
**主要用途**: 提供实时协作编辑、版本管理、权限控制的在线文档平台

### 技术栈与架构（必填字段）
- **主要语言**: TypeScript 5.0, Node.js 20
- **框架/库**: React 18, Next.js 14, Express 4.18, Socket.io 4.6
- **数据库**: MongoDB 7, Redis 7, Elasticsearch 8
- **部署环境**: Kubernetes, Docker, AWS EKS
- **CI/CD**: GitHub Actions, ArgoCD

### 核心模块说明（必填字段）
- **模块1**: 文档编辑器 - 基于 Quill.js 的富文本编辑器
- **模块2**: 实时协作引擎 - WebSocket + OT算法实现冲突解决
- **模块3**: 权限管理服务 - 文档级/段落级细粒度权限控制
- **模块4**: 版本控制服务 - 文档版本快照、历史回溯、差异对比
- **模块5**: 搜索服务 - 全文检索、智能推荐
```

---

### 示例 3: 数据处理/ETL 项目

```markdown
### 项目基本信息（必填字段）
**项目名称**: 数据仓库ETL管道  
**项目类型**: 数据处理（批处理 + 流处理）  
**主要用途**: 从多数据源抽取、清洗、转换数据并加载到数据仓库

### 技术栈与架构（必填字段）
- **主要语言**: Python 3.11, Scala 2.13
- **框架/库**: Apache Airflow 2.7, Apache Spark 3.5, Pandas 2.1
- **数据库**: PostgreSQL 15 (元数据), ClickHouse 23 (数据仓库), Kafka 3.5
- **部署环境**: Kubernetes, Helm, AWS EMR
- **CI/CD**: Jenkins, GitLab CI

### 核心模块说明（必填字段）
- **模块1**: 数据采集模块 - 从MySQL、Oracle、API等多源采集
- **模块2**: 数据清洗模块 - 去重、补全、格式标准化
- **模块3**: 数据转换模块 - 维度建模、事实表生成
- **模块4**: 调度编排模块 - Airflow DAG编排，任务依赖管理
- **模块5**: 监控告警模块 - 任务失败重试、Slack/钉钉告警
```

---

## 验证方法

### 1. 语法校验

```bash
# 验证 JSON 语法（如果使用外部规则文件）
python3 -m json.tool YL-your-rules.json

# 验证 .copilot-config.json
python3 -m json.tool .github/.copilot-config.json
```

### 2. 运行 CI 校验

```bash
# 本地模拟 CI 校验
cd .github
python3 workflows/validate-copilot-config.yml
```

### 3. 查看生成的规则快照

```bash
# 查看最终生效的规则
cat .github/logs/calc-effective-rules.json

# 查看 rules_source（应为 external / gitc+internal / internal_absolute）
jq -r '.rules_source' .github/logs/calc-effective-rules.json

# 查看 fallback_reason（如果有回退）
jq -r '.fallback_reason' .github/logs/calc-effective-rules.json
```

### 4. 测试 Copilot 行为

1. 在 VS Code 中打开项目
2. 重新加载窗口: `Cmd/Ctrl + Shift + P` → `Developer: Reload Window`
3. 使用 Copilot Chat 测试: `@workspace 分析我的项目结构`
4. 观察 Copilot 是否按照 gitc.md 中的规则提供建议

---

## 常见问题

### Q1: 必须填写所有字段吗？

**A**: 不必须。占位字段分为两类：
- **必填字段**（项目基本信息、技术栈、核心模块）：强烈建议填写，帮助 Copilot 理解项目
- **可选字段**（自定义规范、路径规则等）：留空使用默认配置即可

### Q2: 留空的占位符会影响功能吗？

**A**: 不会。留空时系统会：
- `external_rules_file` 留空 → 使用 gitc.md 描述 + 内置规则
- 其他可选字段留空 → 使用默认配置

### Q3: 如何知道我的配置生效了？

**A**: 三种验证方法：
1. 查看 `.github/logs/calc-effective-rules.json` 的 `rules_source` 字段
2. 使用 Copilot Chat 询问项目信息，观察回答是否符合配置
3. 运行 CI 工作流，检查是否有错误日志

### Q4: 可以同时使用 gitc.md 和外部 JSON 规则吗？

**A**: 可以，但优先级如下：
- 如果 `external_rules_file` 配置且有效 → 外部 JSON 作为绝对规则
- 外部文件无效或未配置 → gitc.md 描述 + 内置规则

### Q5: 如何修改已填写的字段？

**A**: 直接编辑 `gitc.md` 文件，保存后：
1. 提交到 Git 触发 CI 校验
2. VS Code 重新加载窗口
3. 查看新的规则快照确认生效

---

## 快速检查清单

在提交配置前，请检查以下项：

- [ ] **external_rules_file** 已填写或确认留空
- [ ] 如填写外部文件，确认：
  - [ ] 文件在项目根目录（与 .github 同级）
  - [ ] 文件名以 YL/yl 开头
  - [ ] JSON 格式有效
- [ ] **项目基本信息** 三项（名称/类型/用途）已填写
- [ ] **技术栈** 五项已填写
- [ ] **核心模块** 至少列出 3 个
- [ ] 可选字段根据需要填写或留空
- [ ] 运行 `python3 -m json.tool` 验证 JSON 语法（如有）
- [ ] 提交后查看 CI 日志确认无错误

---

**最后更新**: 2025-12-13  
**相关文档**: 
- `gitc.md` - 项目绝对规则文档
- `README.md` - 配置模板说明
- `COPILOT_QUICK_START.md` - 快速上手指南
