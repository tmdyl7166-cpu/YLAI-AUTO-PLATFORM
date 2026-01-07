# GitHub Copilot 编程语言配置指南

**配置文件**: `.copilot-config.json`  
**版本**: 1.0.0  
**创建日期**: 2025-12-13  
**特性**: 完全便携、自动识别、无需编译  
**当前存放位置**: 本模板位于仓库根目录的 `.github/` 下，复制到目标项目根目录后生效；无论 `.github` 上级目录名称为何，均以其上级目录为项目根目录进行执行和指向；`.github` 目录内的所有 `.json` 配置均需识别并视为 Copilot 绝对规则；根目录下的规则（任意名称的 `.json` 配置）仅针对该根目录对应的项目生效。文中提到的外部示例文件（如 YLAI-AUTO/*）在此模板中不存在，仅为示例。外部规则文件若使用，必须与 `.github` 同级且文件名以 YL/yl 开头并为有效 JSON。
**内容优化要求**: 每次优化需对全量修改内容进行整体逻辑梳理与整理，保持结构不变，仅优化表述与一致性，确保无逻辑冲突。
**内容优化执行步骤**:
1) 获取任务与全局描述，先用中文复述；
2) 给出精简方案/变更要点清单，等待确认；
3) 执行修改（不改结构，只调表述/一致性），复核逻辑无冲突；
4) 提供全文更新结果并询问是否需再调整。
**内容联动优化规则**: 每次优化需同步审视相关配置与上下文文件，一并优化；优化后检查配置是否重复、指向路径是否正确。
**自动修复策略**: 部署脚本或优化内容后如出现错误，无需询问，自动多维度迭代修复直至任务正常运行，再反馈结果。
**“整理验证” 关键词**: 执行该指令时需对所有功能与配置进行双向联动的全量识别与验证，绝不遗漏，确保无冲突、无重复；要求：
1) 覆盖 `.github` 与根目录全部配置（含隐藏目录与全部文件类型，逐行检查）；
2) 双向检查：配置指向与被指向路径/文件均需匹配且无缺失；
3) 冲突/重复判定：相同键/路径/规则若冲突或重复，需给出消解方案；
4) 输出完整报告：列出检查范围、发现项、修复动作与剩余风险。
**“提出建议” 关键词**: 触发时需基于全局内容联动提出多维度扩展性优化建议，覆盖跨文件/配置/上下文的改进点，保持一致性、可移植性、无冲突、无重复。

---

## 📋 概述

这是一个**独立的、可移植的** GitHub Copilot 配置文件。您可以将其放在任何项目目录中，Copilot 会根据当前目录的内容自动识别项目结构、编程语言、框架和最佳实践，从而提供精准的代码建议。

### ✨ 核心特性
3. **独立便携** - 完全独立的配置文件，可复制到任何项目
4. **零编译** - 纯配置文件，不需要编译、构建或初始化过程

## 🚀 快速开始
### 方案 1：项目根目录部署（推荐）

```bash

# Copilot 会自动加载配置

```bash
```

# 放在用户主目录（影响所有项目）
mkdir -p ~/.copilot
cp .copilot-config.json ~/.copilot/config.json
```

---

## 🔍 配置说明

### 1. 项目自动发现 (`projectDiscovery`)

配置会自动扫描当前目录及所有子目录，识别：
- 所有源代码文件
- 配置文件（package.json、pyproject.toml、pom.xml 等）
- 项目结构（src、backend、frontend 等）
- 编程语言和框架

```json
{
  "projectDiscovery": {
    "enabled": true,
    "scanDepth": "unlimited",
    "patterns": {
      "fileExtensions": ["支持的文件类型"],
      "configFiles": ["配置文件识别"],
      "directories": ["特定目录识别"]
    }
  }
}
```

### 2. 语言规则 (`languageRules`)

针对不同编程语言的专门规则：

- **Python**: snake_case、4空格缩进、Google风格文档字符串
- **JavaScript/TypeScript**: camelCase、2空格缩进、严格类型检查
- **Java**: PascalCase、4空格缩进、Maven/Gradle依赖检查
- **Go**: mixedCase、Tab缩进、Goroutine和Channel分析
- **Shell**: snake_case、2空格缩进、严格错误处理
- **HTML/CSS**: 语义化标记、WCAG 2.1无障碍标准

### 3. 代码生成规则 (`codeGenerationRules`)

**优先级顺序**：
1. ✅ **重用现有代码** - 优先优化和改进现有脚本
2. ✅ **一致性检查** - 确保新代码与现有代码风格一致
3. ✅ **去重检测** - 识别并消除重复代码
4. ✅ **创建新文件** - 仅在无法复用时才创建新文件

```json
{
  "codeGenerationRules": {
    "optimization": {
      "reuseExistingCode": {
        "enabled": true,
        "priority": "highest"
      }
    }
  }
}
```

### 4. Copilot 行为控制 (`copilotBehavior`)

- **自然语言处理** - 使用语义相似度匹配（阈值 0.75）
- **分析深度** - 无限制地扫描项目所有文件
- **上下文窗口** - 使用整个项目作为上下文
- **质量保证** - 自动验证逻辑、兼容性和测试建议

### 5. 项目上下文推理 (`projectContextInference`)

自动识别以下项目模式：
- **单体应用** vs **微服务**
- **前后端分离**
- **插件系统**
- **Docker 部署**
- **CI/CD 流程**

---

## 💡 使用场景

### 场景 1：添加新功能
```
用户请求: "在 backend/api/user.py 中添加用户搜索功能"

Copilot 会自动：
1. 扫描现有的 user.py 和相关模块
2. 识别现有的代码模式和约定
3. 查找相似的功能（如排序、分页）
4. 提供基于现有代码风格的新功能建议
5. 检查与数据库、日志、认证的集成
```

### 场景 2：优化现有代码
```
用户请求: "优化 scripts/data_processor.py"

Copilot 会自动：
1. 分析 data_processor.py 的全部内容
2. 查找相同目录或相关目录中的类似脚本
3. 识别性能瓶颈和代码重复
4. 建议复用其他脚本的优化代码
5. 保持与其他脚本的一致性
```

### 场景 3：跨语言项目
```
项目包含: Python backend + React frontend + Go 微服务

Copilot 会自动：
1. 识别三种语言和对应的最佳实践
2. 维护跨服务的 API 一致性
3. 检查数据格式（JSON、Protocol Buffer）的兼容性
4. 建议在各服务间使用统一的错误处理
```

---

## 🎯 关键功能详解

### 自动识别相似代码

```python
# 现有脚本: scripts/utils.py
def format_date(date_str):
    """格式化日期"""
    # 现有实现...

# 新请求: 在另一个脚本中添加类似功能
# Copilot 会自动：
# ✅ 发现现有的 format_date 函数
# ✅ 建议复用而不是重写
# ✅ 提供参数扩展建议
```

### 跨文件一致性检查

```
当修改配置时：
✅ 检查依赖配置目录中的相同设置
✅ 验证所有指向该配置的引用
✅ 更新相关的脚本和文档
✅ 确保所有模块的配置指向正确
```

### 深度项目分析

```
即使对于大型项目：
✅ 扫描无限深度的目录
✅ 分析所有源代码文件
✅ 提取项目架构关系
✅ 识别模块间的依赖
✅ 生成准确的代码建议
```

---

## 优先级与决策逻辑（与配置一致）
- 应用顺序：`external_rules_file (YL*/根级/JSON 有效)` → `gitc.md 描述` → `.github/.copilot-config.json (默认/回退绝对规则)` → `.github/*.json` → `<root>/*.json`。
- 决策说明：
  - external_rules_file 如命名非 YL/yl、位置非根级、文件缺失或 JSON 无效，记录 E002/E003/E004/E005 并回退 `.github/.copilot-config.json` 为绝对规则。
  - 未配置外部文件时，使用 gitc.md 文档描述；内置规则库提供基础定义。
  - 其后才应用根目录的其他 `.json` 配置（受上述优先级覆盖）。

---

## 🔐 忽略规则

配置会自动忽略以下目录和文件，提高分析速度：

```
node_modules/          # NPM 依赖
.git/                  # Git 版本库
.venv/, venv/         # Python 虚拟环境
__pycache__/          # Python 缓存
dist/, build/         # 构建输出
target/               # Java 构建
vendor/               # Go 依赖
.pytest_cache/        # 测试缓存
coverage/             # 覆盖率数据
*.log                 # 日志文件
```

---

## 📊 配置优先级

当多个配置文件存在时，优先级如下：

1. **项目根目录** `.copilot-config.json` (最高)
2. **工作区目录** `.copilot/config.json`
3. **用户主目录** `~/.copilot/config.json`
4. **内置默认配置** (最低)

---

## ✅ 验证配置

配置包含自验证机制：

```json
{
  "selfValidation": {
    "enabled": true,
    "checkConfigSyntax": true,
    "validatePatterns": true,
    "testDiscoveryMechanisms": true,
    "reportAnomalies": true
  }
}
```

### 手动验证步骤

1. **在 VS Code 中打开项目**
2. **打开 Copilot Chat** (`Ctrl+Shift+I`)
3. **输入命令**:
   ```
   @workspace 分析我的项目结构和主要编程语言
   ```
4. **验证输出**：
   - ✅ 正确识别的编程语言
   - ✅ 准确的项目结构分析
   - ✅ 识别出的框架和依赖

---

## 🛠️ 常见使用场景

### 场景 A：Python 项目
```
配置会自动：
- 检测 requirements.txt、pyproject.toml、setup.py
- 应用 PEP 8 命名约定（snake_case）
- 启用类型提示验证
- 生成 Google 风格文档字符串
```

### 场景 B：Node.js/React 项目
```
配置会自动：
- 检测 package.json 和 React/Vue/Angular 框架
- 应用 JavaScript 约定（camelCase）
- 启用 ESLint 规则验证
- 检查异步/等待和 Promise 链
```

### 场景 C：全栈项目（Python + React）
```
配置会自动：
- 同时分析 backend 和 frontend
- 验证 API 调用的一致性
- 检查数据格式兼容性
- 建议跨层级的优化
```

---

## 🚨 故障排除

### 问题：Copilot 没有识别我的项目

**解决方案**：
1. 确保 `.copilot-config.json` 在项目根目录
2. 重启 VS Code：`Cmd+Shift+P` → `Developer: Reload Window`
3. 检查是否有根目录标记文件（package.json 或 .git）

### 问题：配置识别不了某个文件类型

**解决方案**：
1. 检查文件是否在 `ignorePatterns` 中
2. 将文件扩展名添加到对应的 `languageRules` 中
3. 修改配置后重启 Copilot

### 问题：生成的代码与项目风格不符

**解决方案**：
1. 验证 `languageRules` 中的约定是否正确
2. 在 Copilot Chat 中明确说明风格要求
3. 查看是否有其他全局配置冲突

---

## 📝 配置修改指南

如需自定义配置，可修改以下关键字段：

### 添加新的文件类型支持
```json
{
  "languageRules": {
    "newLanguage": {
      "enabled": true,
      "filePatterns": ["*.ext"],
      "conventions": {
        "naming": "style"
      }
    }
  }
}
```

### 调整扫描范围
```json
{
  "projectDiscovery": {
    "patterns": {
      "ignorePatterns": ["添加要忽略的目录"]
    }
  }
}
```

### 修改优先级
```json
{
  "codeGenerationRules": {
    "optimization": {
      "reuseExistingCode": {
        "priority": "highest"
      }
    }
  }
}
```

---

## 🎓 最佳实践

### ✅ 推荐做法
1. **将配置放在项目根目录** - 所有贡献者都能使用
2. **定期检查识别结果** - 确保 Copilot 理解您的项目
3. **在 Copilot Chat 中验证** - 确认分析的准确性
4. **提供上下文** - 在请求中说明文件路径和目的

### ❌ 避免做法
1. **不要修改核心发现逻辑** - 除非您完全理解影响
2. **不要忽略重要目录** - 可能导致分析不完整
3. **不要依赖缓存过期数据** - 定期重启以刷新

---

## 📞 支持信息

- **配置类型**: GitHub Copilot 编程语言配置
- **兼容版本**: GitHub Copilot 1.0+
- **支持语言**: 10+ 种编程语言
- **可靠性**: 产品级别

---

## 📄 许可证

此配置文件可自由使用和修改。

---

**最后更新**: 2025-12-13  
**状态**: ✅ 即用型配置
