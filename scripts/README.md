# 脚本文档

本文档描述了 YLAI-AUTO-PLATFORM 项目 `YLAI-AUTO-PLATFORM/scripts/` 文件夹中的所有脚本。

## 概述

脚本按类别组织：启动脚本、检查和验证脚本、生成和工具脚本。所有脚本设计为独立运行，避免代码重复。

## 启动脚本

### dev-start.sh
**目的**：启动包含后端和前端服务的开发环境。

**用法**：
```bash
YLAI-AUTO-PLATFORM/scripts/dev-start.sh
```

**功能**：
- 如果不存在，则创建 Python 虚拟环境
- 安装后端依赖
- 使用 uvicorn 在端口 8001 上启动后端，支持自动重载
- 如需要，安装前端依赖
- 使用 npm 在端口 3001 上启动前端
- 等待服务就绪
- 提供访问 URL

**端口**：
- 后端：http://0.0.0.0:8001
- 前端：http://0.0.0.0:3001

### run_backend.sh
**目的**：仅启动后端服务。

**用法**：
```bash
YLAI-AUTO-PLATFORM/scripts/run_backend.sh
```

**环境变量**：
- HOST：默认 0.0.0.0
- PORT：默认 8001
- RELOAD：设置以启用重载
- ONECLICK_LOG：日志文件路径

## 检查和验证脚本

### auto_checks.sh
**目的**：运行基础健康检查并将摘要追加到 README.md。

**用法**：
```bash
YLAI-AUTO-PLATFORM/scripts/auto_checks.sh
```

**环境变量**：
- API_PORT：默认 8001
- WEB_PORT：默认 8080
- API_TARGET：默认 http://127.0.0.1:${API_PORT}

### run_full_checks.sh
**目的**：运行全面检查，包括健康、API、页面、WS 和 E2E 测试。

**用法**：
```bash
YLAI-AUTO-PLATFORM/scripts/run_full_checks.sh
```

**环境变量**：
- BASE_URL：默认 http://127.0.0.1:8001
- CHECK_TIMEOUT：默认 3.0
- WS_STRICT：设置为 1 以进行严格 WS 检查

### probe_health.sh
**目的**：探测 /health 端点。

**用法**：
```bash
YLAI-AUTO-PLATFORM/scripts/probe_health.sh
```

### checks_apis_accept401.py
**目的**：检查 API 端点，接受 401 响应。

**用法**：
```bash
YLAI-AUTO-PLATFORM/scripts/checks_apis_accept401.py
```

### validate_pages.py
**目的**：验证静态页面。

**用法**：
```bash
YLAI-AUTO-PLATFORM/scripts/validate_pages.py
```

### probe_ws.py
**目的**：探测 WebSocket 连接。

**用法**：
```bash
YLAI-AUTO-PLATFORM/scripts/probe_ws.py
```

### e2e_dag_sample.py
**目的**：运行 E2E DAG 示例测试。

**用法**：
```bash
YLAI-AUTO-PLATFORM/scripts/e2e_dag_sample.py
```

## 生成和工具脚本

### gen_api_map_json.py
**目的**：生成 API 映射 JSON。

### gen_container_deps_md.py
**目的**：生成容器依赖 Markdown。

### gen_from_spec.py
**目的**：根据规范生成代码。

### audit_docs.py
**目的**：审核文档。

### check_registry_linkage.py
**目的**：检查注册表链接。

### consistency_check.py
**目的**：执行一致性检查。

### mapping_validator.py
**目的**：验证映射。

### validate_project_integrity.py
**目的**：验证项目完整性。

### validate_tasks.py
**目的**：验证任务。

### env_check.py
**目的**：检查环境。

### env_install.sh
**目的**：安装环境依赖。

### auto_detect_env.sh
**目的**：自动检测环境。

### select_model.sh
**目的**：选择 AI 模型。

### setup-multi-models.sh
**目的**：设置多个模型。

### ensure_model.sh
**目的**：确保模型可用性。

### repair_pages.py
**目的**：修复页面（默认干运行）。

### strip_page_js.py
**目的**：从页面剥离 JS。

### inject_assets.py
**目的**：注入资源。

### create-files.sh
**目的**：创建必要文件。

### cleanup.sh
**目的**：清理临时文件。

### cleanup_stacks.sh
**目的**：清理栈。

### quick_optimize.sh
**目的**：快速优化。

### ci_container_deps_check.sh
**目的**：CI 容器依赖检查。

### local_security_scan.sh
**目的**：本地安全扫描。

### pages_consistency_report.sh
**目的**：页面一致性报告。

### probe_front_pages.sh
**目的**：探测前端页面。

### watch_front_pages.sh
**目的**：监视前端页面。

### auto_web_opener.py
**目的**：自动打开网页。

### bash_completion.sh
**目的**：Bash 补全设置。

### completion.sh
**目的**：命令补全。

### hx.py
**目的**：HTMX 相关脚本。

### hx.sh
**目的**：HTMX shell 脚本。

### vpn_openvpn.sh
**目的**：使用 OpenVPN 设置 VPN。

### full_suite.py
**目的**：完整测试套件。

### full_suite_8003.py
**目的**：端口 8003 上的完整测试套件。

### global_config_manager.py
**目的**：管理全局配置。

### scan_container_deps.py
**目的**：扫描容器依赖。

### dedupe_completed_task.py
**目的**：去重已完成任务。

### check_services.py
**目的**：检查服务。

### 识别_old.py
**目的**：旧识别脚本（已弃用）。

## 注意事项

- 所有脚本假设从项目根目录运行或使用相对路径。
- Python 脚本需要激活虚拟环境。
- 启动脚本自动处理依赖安装。
- 检查脚本输出到 logs/ 文件夹。
- 没有脚本具有重复功能；每个脚本服务于独特目的。