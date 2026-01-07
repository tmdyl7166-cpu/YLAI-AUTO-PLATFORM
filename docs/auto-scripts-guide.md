# 自动化运行脚本说明

本说明文档用于梳理 YLAI-AUTO-PLATFORM 项目根目录及主要子目录下所有已部署的自动化脚本及其启动方式、功能说明、适用场景。

---

## 1. YLAI-AUTO-PLATFORM/scripts/validate_project_integrity.py
- **功能**：递归扫描项目所有文件，校验 API、脚本、文档、引用、文件位置等内容是否与 docs/统一接口映射表.md 保持一致，自动迁移错误位置文件并修复引用，生成整理验证报告。
- **启动方式**：
  ```bash
  python3 YLAI-AUTO-PLATFORM/scripts/validate_project_integrity.py
  ```
- **输出**：生成/更新 docs/全局内容验证报告.md，自动归档校验结果。
- **适用场景**：项目结构优化、内容同步、批量修复、CI自动校验。

## 2. auto-start.sh
- **功能**：一键启动后端与前端服务，自动激活虚拟环境、安装依赖、启动 FastAPI 与前端开发服务器。
- **启动方式**：
  ```bash
  bash auto-start.sh
  ```
- **输出**：后端服务监听 8001 端口，前端服务监听 3001 端口。
- **适用场景**：本地开发、快速联调、环境初始化。

## 3. start.sh
- **功能**：简化版一键启动脚本，激活虚拟环境并启动后端服务。
- **启动方式**：
  ```bash
  bash start.sh
  ```
- **输出**：后端服务监听 8001 端口。
- **适用场景**：后端单独开发或调试。

## 4. ai-docker/run.sh / start_ai_platform.sh / stop_ai_platform.sh / restart_ai_platform.sh
- **功能**：AI平台容器化部署与管理，支持启动、停止、重启多模型服务。
- **启动方式**：
  ```bash
  bash ai-docker/start_ai_platform.sh
  bash ai-docker/stop_ai_platform.sh
  bash ai-docker/restart_ai_platform.sh
  bash ai-docker/run.sh
  ```
- **输出**：容器化多模型服务，支持分布式与多节点。
- **适用场景**：AI平台部署、模型服务运维、容器化管理。

## 5. test_auth.sh
- **功能**：后端鉴权接口自动化测试。
- **启动方式**：
  ```bash
  bash test_auth.sh
  ```
- **输出**：鉴权接口测试结果。
- **适用场景**：接口安全性验证、自动化测试。

## 6. YLAI-AUTO-PLATFORM/scripts/checks_apis_accept401.py
- **功能**：API接口自动化健康检查，支持 401 响应容忍。
- **启动方式**：
  ```bash
  python3 YLAI-AUTO-PLATFORM/scripts/checks_apis_accept401.py
  ```
- **输出**：API健康检查结果。
- **适用场景**：API上线前健康验证、自动化监控。

## 7. docker/ 相关脚本
- **功能**：容器编排与服务部署，支持多环境 docker-compose 启动。
- **启动方式**：
  ```bash
  docker-compose -f docker/docker-compose.yml up
  docker-compose -f docker/docker-compose.dev.yml up
  docker-compose -f docker/docker-compose.ai-dev.yml up
  docker-compose -f docker/docker-compose.prod.yml up
  ```
- **输出**：多服务容器化部署。
- **适用场景**：生产环境、开发环境、AI服务环境部署。

---

> 所有自动化脚本建议结合 CI/CD 流程定期运行，确保内容一致性与部署安全性。
> 如需扩展脚本功能或新增自动化校验，请同步更新本说明文档。
