# Copilot 快速上手

## 配置扩展速览
- `languageRulesExtension`: 扩展语言与框架规则（Rust/Ruby/PHP/Swift/Kotlin；React/Vue/Angular；Django/Flask；Spring Boot）。
- `errorHandling`: 三层错误级别（fatal/warning/info），日志目录 `/.github/logs/`，错误码体系（E001/E002/E003/W001/I001）。
- `testingAndValidation`: 自检命令与校验工具（`python3 -m json.tool .github/.copilot-config.json`，`jsonschema`），CI 示例（GitHub Actions）。
- `documentationAndExamples`: 快速诊断流程、迁移指南（从 `.cursorrules`/`.windsurfrules`）、教程链接。
- `versionManagement`: `schemaVersion: "1.0.0"`，`CHANGELOG.md`，两周期（≈6个月）弃用策略。
- `communityAndExtensions`: 自定义插件钩子（`onBeforeScan`/`onAfterOptimize`），PR 贡献要求（测试+文档），Issues/Discussions 反馈渠道。

### 快速验证
```bash
python3 -m json.tool .github/.copilot-config.json
```

更多细节见 `.github/.copilot-config.json` 与配置指南。# Copilot 配置快速参考

## 📦 配置文件信息

| 属性 | 值 |
|------|-----|
| 文件名 | `.copilot-config.json` |
| 位置 | 本模板存放于仓库的 `.github/` 目录，复制到目标项目根目录后生效；无论 `.github` 上级目录名称为何，均以其上级目录为项目根目录执行；`.github` 目录内的所有 `.json` 配置均视为 Copilot 绝对规则；如配置 external_rules_file，必须与 `.github` 同级且文件名以 YL/yl 开头且 JSON 有效 |
| 内容优化要求 | 每次优化需对全量修改内容进行整体逻辑梳理与整理，保持结构不变，仅优化表述与一致性，确保无逻辑冲突 |
| 内容优化执行步骤 | 1) 获取任务与全局描述，先用中文复述；2) 给出精简方案/变更要点清单，等待确认；3) 执行修改（不改结构，只调表述/一致性），复核逻辑无冲突；4) 提供全文更新结果并询问是否需再调整 |
| 内容联动优化规则 | 每次优化需同步审视相关配置与上下文文件，一并优化；优化后检查配置是否重复、指向路径是否正确 |
| 自动修复策略 | 部署脚本或优化内容后如出现错误，无需询问，自动多维度迭代修复直至任务正常运行，再反馈结果 |
| “整理验证” 关键词 | 执行该指令时需对所有功能与配置进行双向联动的全量识别与验证，绝不遗漏，确保无冲突、无重复；要求：1) 覆盖 `.github` 与根目录全部配置（含隐藏目录与全部文件类型，逐行检查）；2) 双向检查配置指向与被指向路径/文件均匹配无缺失；3) 冲突/重复时给出消解方案；4) 输出完整报告（范围、发现、修复、剩余风险） |
| “提出建议” 关键词 | 触发时需基于全局内容联动提出多维度扩展性优化建议，覆盖跨文件/配置/上下文的改进点，保持一致性、可移植性、无冲突、无重复 |
| 大小 | 自包含 |
| 编译需求 | 无 |
| 初始化需求 | 无 |
| 便携性 | 完全便携 |
| 自动识别 | ✅ 是 |
| 动态适应 | ✅ 是 |

---

## 🎯 核心功能速览

### 1. 自动识别 (Auto-Discovery)
```
放入目录 → 自动扫描 → 识别语言 → 应用规则
```

### 2. 智能复用 (Code Reuse)
```
检测相似代码 → 建议复用 → 避免重复 → 保持一致
```

### 3. 深度分析 (Deep Analysis)
```
无限扫描深度 → 全面理解 → 精准建议 → 上下文感知
```

### 4. 无编译部署 (Plug & Play)
```
复制配置文件 → 刷新编辑器 → 立即生效 → 无需构建
```

---

## 🚀 3 秒快速开始

### 步骤 1：复制配置文件
```bash
cp .github/.copilot-config.json /path/to/your/project/
```

### 步骤 2：刷新编辑器
```
VS Code: Cmd+Shift+P → "Developer: Reload Window"
```

### 步骤 3：开始使用
```
Copilot 自动识别您的项目并提供建议
```

---

## 📋 支持的编程语言

| 语言 | 优先级 | 关键文件 | 约定 |
|------|--------|---------|------|
| Python | 10 | main.py, app.py | snake_case, 4空格 |
| TypeScript | 10 | index.ts, app.ts | camelCase, 2空格 |
| JavaScript | 9 | index.js, app.js | camelCase, 2空格 |
| Java | 10 | Main.java, App.java | PascalCase, 4空格 |
| Go | 9 | main.go | mixedCase, Tab |
| Shell | 7 | main.sh, start.sh | snake_case, 2空格 |
| HTML | 8 | *.html | 语义化标记 |
| CSS/SCSS | 7 | *.css, *.scss | kebab-case, 2空格 |

---

## 🔍 自动发现的项目类型

### 配置文件识别
```
package.json      → Node.js/React/Vue 项目
pyproject.toml    → Python 项目
pom.xml           → Java Maven 项目
build.gradle      → Java Gradle 项目
go.mod            → Go 项目
Cargo.toml        → Rust 项目
docker-compose.yml → Docker 部署
```

### 目录结构识别
```
frontend/         → Web 前端
backend/          → 后端服务
src/              → 源代码
tests/            → 测试代码
scripts/          → 脚本文件
docker/           → Docker 配置
docs/             → 文档
```

---

## ⚙️ 关键配置项

### 代码生成优先级
```
1. 优化现有脚本 (最高)
   ↓
2. 检查一致性
   ↓
3. 检测重复
   ↓
4. 创建新文件 (仅在必要时)
```

### 扫描深度
```
scanDepth: "unlimited"  → 扫描所有子目录
recursiveAnalysis: true → 深度代码分析
contextWindow: "full_project" → 整个项目作为上下文
```

### 忽略规则
```
自动忽略:
- node_modules/     (NPM 依赖)
- .git/             (版本库)
- .venv/            (虚拟环境)
- __pycache__/      (缓存)
- dist/             (构建输出)
- *.log             (日志)
```

---

## 💬 Copilot Chat 示例命令

### 命令 1: 分析项目结构
```
@workspace 分析我的项目结构，列出所有主要模块和编程语言
```

### 命令 2: 优化现有脚本
```
@workspace 在 scripts/process.py 目录下寻找相似的脚本，
建议如何优化 process.py，优先复用现有代码
```

### 命令 3: 跨文件一致性检查
```
@workspace 检查 config/ 目录下的所有配置文件是否一致，
并建议统一的配置方案
```

### 命令 4: 生成新功能
```
在 backend/api/user.py 中添加用户搜索功能，
确保与现有的认证、日志、错误处理保持一致
```

---

## 🎨 输出示例

### 扫描到的项目信息
```
项目类型: Full-Stack (Python Backend + React Frontend)
编程语言:
  - Python: 65% (backend/, scripts/)
  - JavaScript: 35% (frontend/, config/)

主要框架:
  - Backend: Flask/FastAPI
  - Frontend: React
  - Database: PostgreSQL

发现的模块:
  ✓ API 服务
  ✓ 认证系统
  ✓ 数据处理
 
  ---

  ## 项目规则优先级与回退
  - external_rules_file（须以 YL/yl 开头、与 .github 同级、JSON 有效）为最高优先级；验证失败或缺失即记录错误码并回退。
  - 未配置或校验失败时，使用 `gitc.md` 描述；回退绝对规则为 `.github/.copilot-config.json`。
  - 其后才应用 `.github/*.json` 与根目录其他 `.json` 配置（受上述优先级覆盖）。

  ### 占位字段对应
  - 见 `.github/.copilot-config.json` 的 `placeholders`，与 `gitc.md` 字段一一对应。

  ### 校验命令
  ```bash
  python3 -m json.tool .github/.copilot-config.json
  ```
  ✓ 日志记录
  ✓ 错误处理
```

### 代码建议示例
```
当您说: "优化数据处理"

Copilot 会:
1. 查找现有的数据处理脚本
2. 识别性能瓶颈
3. 发现可复用的工具函数
4. 建议改进方案
5. 检查与其他模块的兼容性

输出: 一个完整的优化方案，包含：
  ✓ 改进的代码
  ✓ 可复用的函数
  ✓ 测试建议
  ✓ 性能对比
```

---

## 🔧 常见自定义

### 添加新语言支持
```json
在 languageRules 中添加:
{
  "rust": {
    "enabled": true,
    "filePatterns": ["*.rs"],
    "conventions": {
      "naming": "snake_case"
    }
  }
}
```

### 修改扫描范围
```json
"ignorePatterns": [
  "node_modules",
  "自定义目录"
]
```

### 调整匹配阈值
```json
"naturalLanguageProcessing": {
  "threshold": 0.75  // 0-1, 越高越严格
}
```

---

## 📊 性能特性

| 特性 | 说明 |
|------|------|
| **扫描深度** | 无限制 |
| **缓存机制** | 自动缓存（TTL: 1小时） |
| **启动时间** | < 100ms |
| **内存占用** | 轻量级 |
| **CPU 影响** | 最小化 |
| **网络依赖** | 仅需 Copilot 连接 |

---

## ✅ 验证清单

部署后请检查：

- [ ] 配置文件在项目根目录
- [ ] VS Code 已重启
- [ ] GitHub Copilot 扩展已启用
- [ ] 在 Copilot Chat 中能看到 @workspace
- [ ] 文件识别准确（通过 Chat 验证）
- [ ] 代码建议相关且准确
- [ ] 没有权限错误

---

## 🐛 调试技巧

### 查看识别的项目信息
```
在 Copilot Chat 中:
@workspace 告诉我你识别到的文件类型和项目结构
```

### 强制刷新缓存
```
VS Code:
1. Cmd+Shift+P
2. "Developer: Reload Window"
```

### 检查配置文件
```bash
# 验证 JSON 语法
python3 -m json.tool .copilot-config.json
```

---

## 📞 快速命令速查

```
重启 Copilot:      Cmd+Shift+P → Reload Window
打开 Chat:         Ctrl+Shift+I (Windows/Linux)
打开 Chat:         Cmd+Shift+I (Mac)
快速修复:          Cmd+. (在红线处)
查看文件结构:      Cmd+Shift+E
全文搜索:          Cmd+Shift+F
```

---

## 🎓 学习资源

- **官方文档**: GitHub Copilot 帮助文档
- **Chat 命令**: 在 Chat 中输入 `/help`
- **快捷键**: Cmd+K, Cmd+/ 显示快捷键列表

---

**最后更新**: 2025-12-13  
**配置版本**: 1.0.0  
**状态**: ✅ 即用型
