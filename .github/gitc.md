
# 项目绝对规则文档 (gitc.md)

**文档性质**: 本文件是项目的**绝对规则描述文档**，所有 Copilot 行为与代码优化均需严格遵循此文档内容  
**作用域**: 
- **本项目自身**（无父目录时）：仅 `.github/` 目录内容
- **检测到父目录时**：自动扩展至父目录及其下所有同级目录、脚本、文档
**优先级**: **最高优先级**，高于任何其他配置文件  
**动态识别机制**:
1. **父目录检测**：系统自动检测 `.github` 是否存在父目录
2. **作用域扩展**：若父目录存在，则规则自动作用于父目录下的所有内容
3. **外部规则识别**：父目录下以 `YL`/`yl` 开头的 `.json` 文件可被识别为绝对规则（由本文档头部 `external_rules_file` 配置）
**验证与回退流程**:
1. 优先识别本文档中指定的外部 `.json` 规则文件（在父目录下查找，与 `.github` 同级）。
2. 如未指定外部文件，则本文档描述的内容作为项目绝对规则。
3. 如指定但校验失败（命名/路径/存在/JSON 语法任一不满足），记录错误并**回退到 `.github/.copilot-config.json` 作为绝对规则**；本文件仍提供描述性补充。
## 📌 外部规则配置指向

### 必填字段（请填写或保持留空）
```json
{
  "external_rules_file": ""
}
```
**填写说明**:
- 留空 `""`: 使用 gitc.md 文档描述 + 内置规则（推荐）
- 填写路径: 必须满足以下所有要求

### 外部文件要求
1. **位置要求**: 文件必须与 `.github/` 处于同一层级（项目根目录）
2. **命名要求**: 文件名必须以 `YL` 或 `yl` 开头（大小写不敏感）
3. **格式要求**: 必须是有效的 JSON 格式文件
-
**有效示例**:
- ✅ `YL-copilot-rules.json` (与 .github/ 同级)
- ✅ `yl_project_config.json` (与 .github/ 同级)
- ✅ `YLconfig.json` (与 .github/ 同级)
- ✅ `ylRules.json` (与 .github/ 同级)
-
**无效示例**:
- ❌ `config/YL-rules.json` (不在项目根目录)
- ❌ `.github/YL-rules.json` (在 .github 内部)
- ❌ `my-rules.json` (未以 YL 开头)
- ❌ `project-YL.json` (YL 不在开头)
-
**规则解析优先级**:
- ✅ **已填写且满足全部校验**: 指定的外部 `.json` 文件作为项目绝对规则。
- ✅ **已填写但校验失败**: 记录错误，回退到 `.github/.copilot-config.json` 作为绝对规则；gitc.md 文档描述继续提供辅助说明。
- ✅ **未填写或留空**: 本 `gitc.md` 文档描述的内容作为项目绝对规则；`.github/.copilot-config.json` 作为内置规则库。
- ℹ️ **内置规则**: `.github/.copilot-config.json` 仅作为默认规则库，提供语言规范、扫描策略等基础定义
-**验证流程**:
-```
-1. 检查 external_rules_file 是否已配置
-   ↓
-2. 如已配置，验证文件名是否以 YL/yl 开头
-   ├─ 否 → 报错：E004 文件名必须以 YL 开头
-   └─ 是 → 继续
-   ↓
-3. 验证文件是否在项目根目录（与 .github 同级）
-   ├─ 否 → 报错：E005 文件必须与 .github 处于同一层级
-   └─ 是 → 继续
-   ↓
-4. 验证文件是否存在
-   ├─ 否 → 报错：E002 外部规则文件不存在
-   └─ 是 → 继续
-   ↓
-5. 验证 JSON 语法
-   ├─ 失败 → 报错：E003 JSON 语法错误
-   └─ 成功 → 加载为项目绝对规则
-```

---

## 1. 项目概览 (Project Overview)

### 项目基本信息（必填字段）
<!-- 请根据实际项目填写以下信息 -->
**项目名称**: `[待填写：如 "用户管理系统" / "数据分析平台"]`  
**项目类型**: `[待填写：如 "Web应用" / "微服务" / "数据处理"]`  
**主要用途**: `[待填写：描述项目的核心功能和业务价值]`

<!-- 模板示例（可删除）-->
<!-- 
**项目名称**: GitHub Copilot 配置模板  
**项目类型**: 可移植的 Copilot 配置与规则集合  
**主要用途**: 提供完整的、自包含的 GitHub Copilot 配置方案，可部署到任何项目
-->

### 技术栈与架构（必填字段）
<!-- 请根据实际项目填写以下信息 -->
- **主要语言**: `[待填写：如 Python 3.11 / Node.js 18 / Java 17]`
- **框架/库**: `[待填写：如 Django 4.2 / React 18 / Spring Boot 3.0]`
- **数据库**: `[待填写：如 PostgreSQL 15 / MongoDB 6 / Redis 7]`
- **部署环境**: `[待填写：如 Docker / Kubernetes / AWS Lambda]`
- **CI/CD**: `[待填写：如 GitHub Actions / GitLab CI / Jenkins]`

<!-- 模板示例（可删除）-->
<!-- 
- **配置格式**: JSON (`.copilot-config.json`) + Markdown (文档)
- **自动化**: GitHub Actions (CI 校验与规则生成)
- **脚本语言**: Python 3 (配置解析与校验)
- **支持语言**: Python, JavaScript, TypeScript, Java, Go, Shell, HTML, CSS, Rust, Ruby, PHP, Swift, Kotlin
-->

### 核心模块说明（必填字段）
<!-- 请列出项目的核心模块及其职责 -->
- **模块1**: `[待填写：如 "用户认证模块 - 负责登录/注册/权限管理"]`
- **模块2**: `[待填写：如 "数据处理模块 - 负责ETL和数据清洗"]`
- **模块3**: `[待填写：如 "API网关 - 统一对外接口和路由"]`
- **模块4**: `[待填写：根据项目实际情况添加]`

<!-- 以下为配置模板专用模块（其他项目可删除）-->
<!-- 
- **配置核心**: `.github/.copilot-config.json` - 内置默认规则定义库
- **规则文档**: `gitc.md` - 项目绝对规则描述文档（本文件）
- **指令集**: `copilot-instructions.md` - AI 代理执行指令
- **工作流**: `workflows/validate-copilot-config.yml` - CI 自动校验
- **文档集**: `COPILOT_*.md` - 配置指南、集成说明、快速开始等
-->

---

## 2. 项目整体运行结构与联动逻辑

### 配置解析流程
```
用户请求 Copilot 优化代码
    ↓
1. 读取 gitc.md (本文档)
    ↓
2. 检查是否配置了 external_rules_file
    ↓
3a. 如已配置且文件存在:
    → 加载外部 .json 规则作为绝对规则
    → .github/.copilot-config.json 仅提供基础语言定义
    ↓
3b. 如未配置或文件不存在:
    → 使用 gitc.md 本文档描述的内容作为绝对规则
    → .github/.copilot-config.json 提供默认实现细节
    ↓
4. 应用规则并执行代码优化/生成
    ↓
5. CI 校验: 生成 .github/logs/calc-effective-rules.json
```

### 关键联动机制
1. **规则优先级**:
   - **最高**: gitc.md 中指定的外部 `.json` 规则文件
   - **次高**: gitc.md 文档本身的描述内容
   - **基础**: `.github/.copilot-config.json` 内置默认规则库

2. **自动发现机制**:
   - Copilot 启动时自动扫描项目根目录的 `gitc.md`
   - 解析 `external_rules_file` 字段，尝试加载外部规则
   - 失败时回退到 gitc.md 文档描述 + 内置规则

3. **CI 校验流程**:
   - 验证 `gitc.md` 语法与结构
   - 检查 `external_rules_file` 指向的文件是否存在
   - 合并最终规则并生成快照文件

### 典型运行命令
- **开发**: 正常使用 VS Code + GitHub Copilot，配置自动生效
- **测试**: `python3 -m json.tool <external_rules_file>` (验证外部规则语法)
- **构建**: 无需构建，配置即用
- **校验**: CI 自动运行或手动执行 workflow

---

## 3. Copilot 执行策略

### 代码生成优先级
1. **重用现有代码** (最高优先级) - 优先优化和扩展现有脚本
2. **一致性检查** - 确保新代码与现有代码风格一致
3. **去重检测** - 识别并消除重复代码
4. **创建新文件** - 仅在无法复用时才创建新文件

### 扫描策略
- **深度**: 无限递归扫描所有子目录（包括隐藏目录）
- **范围**: 解析所有文件类型，逐行完整分析
- **性能**: 大型项目（>10万行）采用增量扫描
- **安全**: 自动跳过 `.env`, `.pem`, `.key`, `secrets/` 等敏感路径

### 内容优化工作流
1. 获取任务并用中文复述全局描述
2. 给出精简方案/变更要点清单，等待确认
3. 执行修改（不改结构，只调表述/一致性）
4. 提供全文更新结果并询问是否需再调整

---

## 4. 语言约定与编码规范

### 默认语言规范
- **Python**: snake_case + 4空格缩进 + Google docstrings
- **JavaScript/TypeScript**: camelCase + 2空格缩进 + 双引号
- **Java**: PascalCase + 4空格缩进 + Javadoc
- **Go**: mixedCase + Tab缩进 + 显式错误处理
- **Shell**: snake_case + 2空格缩进 + `set -e`
- **HTML**: 语义化标签 + WCAG 2.1 无障碍标准
- **CSS**: kebab-case + 2空格缩进

### 自定义覆盖规则（可选字段）
<!-- 如需覆盖上述默认规范，在此填写；留空则使用默认规范 -->
<!-- 示例格式：
- **Python**: 
  - 命名: snake_case（保持默认）
  - 缩进: 2空格（覆盖默认的4空格）
  - 文档: NumPy风格（覆盖默认的Google风格）
-->


---

## 5. 路径包含与排除策略

### 默认包含路径
- `src/**`, `lib/**`, `app/**`, `backend/**`, `frontend/**`
- `scripts/**`, `config/**`, `docs/**`

### 默认排除路径
- `node_modules/**`, `.git/**`, `.venv/**`, `venv/**`, `__pycache__/**`
- `dist/**`, `build/**`, `target/**`, `.next/**`, `.nuxt/**`
- `*.log`, `.DS_Store`, `coverage/**`

### 自定义路径规则
<!-- 如需覆盖默认路径策略，在此填写 -->
```json
{
  "include": [],
  "exclude": []
}
```

---

## 6. 优化重点与质量目标

### 默认优化维度
1. **结构优化** - 改善代码组织与模块化
2. **性能提升** - 识别并优化性能瓶颈
3. **安全加固** - 检测安全漏洞与风险
4. **可维护性** - 提升代码可读性与可维护性
5. **可移植性** - 确保跨平台兼容性
6. **文档完善** - 补充必要的注释与文档

### 自定义优化重点（可选字段）
<!-- 如需指定特定优化重点，在此填写；留空则应用所有默认优化维度 -->
<!-- 示例：
- **优先级1**: 性能优化 - 重点关注数据库查询和API响应时间
- **优先级2**: 安全加固 - 强化输入验证和SQL注入防护
- **优先级3**: 代码复用 - 抽取公共逻辑到工具模块
-->


---

## 7. CI/CD 集成配置

### 校验工作流
- **触发条件**: 每次 push 或 pull request
- **校验内容**:
  1. JSON 语法校验 (`.copilot-config.json` 及外部规则文件)
  2. gitc.md 结构验证
  3. 外部规则文件存在性检查
  4. 最终规则快照生成

### 日志与输出
- **规则快照**: `.github/logs/calc-effective-rules.json`
- **校验日志**: `.github/logs/validation.log`
- **修复日志**: `.github/logs/repair.log`

### 自定义校验配置（可选字段）
<!-- 如需指定自定义 schema 或校验脚本，在此填写；留空则使用默认CI流程 -->
<!-- 示例：
- **自定义 schema**: path/to/custom-schema.json
- **额外校验脚本**: scripts/custom-validation.sh
- **校验触发条件**: 仅在 main 和 develop 分支触发
-->


---

## 8. 自定义钩子与扩展

### 支持的钩子函数
- **onBeforeScan**: 扫描前执行的脚本
- **onAfterOptimize**: 优化完成后执行的脚本

### 钩子配置
<!-- 如需配置钩子，在此填写脚本路径 -->
```json
{
  "onBeforeScan": "",
  "onAfterOptimize": ""
}
```

---

## 9. 关键触发关键词说明

### "整理验证" 关键词
执行该指令时，系统将:
1. 覆盖整个项目的全部配置（含隐藏目录与所有文件类型）
2. 双向检查：配置指向与被指向文件均需匹配且无缺失
3. 冲突/重复判定：给出消解方案
4. 输出完整报告：检查范围、发现项、修复动作、剩余风险

### "提出建议" 关键词
触发时，系统将:
1. 基于全局内容联动提出多维度优化建议
2. 覆盖跨文件/配置/上下文的改进点
3. 保持一致性、可移植性、无冲突、无重复
4. 分级标注优先级（必须/推荐/可选）

### "合并" 关键词
触发时，系统将:
1. 对多个配置文件相同键进行功能唯一性识别
2. 合并重复内容，统一逻辑
3. 生成唯一脚本，清理冗余配置
4. 自动热加载并验证兼容性

---

## 规则总结与使用指南

### 最终规则解析顺序
```
优先级 1 (最高): gitc.md 中指定的 external_rules_file (如存在)
优先级 2: gitc.md 文档本身的描述内容
优先级 3 (默认库): .github/.copilot-config.json 内置规则
```

### 快速查看最终生效规则
```bash
# 查看规则快照
cat .github/logs/calc-effective-rules.json

# 查看路径策略
jq -r '.paths_include_exclude' .github/logs/calc-effective-rules.json

# 查看外部规则文件指向
jq -r '.external_rules_file' .github/logs/calc-effective-rules.json
```

### 使用示例

#### 示例 1: 使用默认规则（无外部配置）
```json
{
  "external_rules_file": ""
}
```
→ 系统使用 gitc.md 文档描述 + .github/.copilot-config.json 默认规则

#### 示例 2: 指定外部规则文件
```json
{
  "external_rules_file": "YL-copilot-rules.json"
}
```
→ 系统加载 YL-copilot-rules.json 作为绝对规则（文件必须在项目根目录）  
→ .github/.copilot-config.json 仅提供语言定义等基础信息

#### 示例 3: 外部规则文件不存在时的回退
```json
{
  "external_rules_file": "YL-non-existent.json"
}
```
→ 系统检测文件不存在，记录 E002 并回退到 `.github/.copilot-config.json` 作为绝对规则  
→ 建议创建有效文件或清空 external_rules_file 以避免重复回退

#### 示例 4: 不符合命名规则的配置（错误）
```json
{
  "external_rules_file": "my-rules.json"
}
```
→ ❌ 报错：E004 文件名必须以 YL 开头  
→ 记录错误并回退到 `.github/.copilot-config.json` 作为绝对规则；需修正文件名

---

## 部署说明

### 作为模板使用
本文件位于 `.github/` 目录中，作为模板提供给其他项目使用。

### 部署到目标项目
1. 将整个 `.github/` 目录复制到目标项目根目录
2. 根据项目需求填写 `gitc.md` 中的各项内容
3. 可选：创建外部规则文件并在 `external_rules_file` 中指定路径
4. 重启 VS Code 或重新加载窗口，配置自动生效

### 验证配置生效
```bash
# 方法 1: 运行 CI 校验
python3 -m json.tool .github/.copilot-config.json

# 方法 2: 查看生成的规则快照
cat .github/logs/calc-effective-rules.json

# 方法 3: 使用 Copilot 进行代码优化，观察是否遵循本文档规则
```

---

**最后更新**: 2025-12-13  
**文档版本**: 2.0.0  
**适用范围**: 所有使用 GitHub Copilot 的项目
