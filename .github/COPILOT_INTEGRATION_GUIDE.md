# Copilot 集成指南
## 与现有流程的集成
- CI 校验：在 GitHub Actions 中运行 JSON 语法与 `jsonschema` 校验，确保 `.github/.copilot-config.json` 合规。
- 日志与错误：统一输出到 `/.github/logs/`；依据错误码进行处理（E001/E002/E003/W001/I001）。
- 版本与兼容：遵循 `metadata.schemaVersion = 1.0.0` 与弃用策略（两周期约 6 个月），维护 `CHANGELOG.md`。

### 优先级与一致性
- 项目规则读取顺序：`gitc.md (external_rules_file 满足校验)` → `gitc.md (描述内容)` → `.github/.copilot-config.json (默认/回退绝对规则)` → `.github/*.json` → `<root>/*.json`。
- 回退策略：external_rules_file 缺失、命名/路径不符或 JSON 无效时，记录错误码（E002/E003/E004/E005），**统一回退到 `.github/.copilot-config.json` 作为绝对规则**。
- 根目录定位：无论仓库放在哪个路径，`.github` 的上级目录即视为项目根；`gitc.md` 放在根，外部规则文件（YL*）与 `.github` 同级即可被识别。
- CI 校验策略：验证 `gitc.md` 的填写项与 `.copilot-config.json` 的 `placeholders` 映射关系一致；留空字段或校验失败均回退到 `.github` 绝对规则。
## 插件与扩展
- 自定义钩子：`onBeforeScan`、`onAfterOptimize` 可用于扫描前/优化后动作。
- 贡献协作：通过 Pull Request，需提供测试用例与文档；讨论与反馈走 Issues/Discussions。
## 语言与框架适配
- 语言扩展：Rust/Ruby/PHP/Swift/Kotlin，遵循各自命名与缩进规则。
- 框架规则：React/Vue/Angular（组件化与现代 API）、Django/Flask（MTV/蓝图）、Spring Boot（分层/DI）。
- 跨语言一致性：接口 `I` 前缀、抽象类 `Abstract` 前缀、JSDoc/Docstring 注释、统一异常类型与日志格式。
## 验证与运行
```bash
python3 -m json.tool .github/.copilot-config.json
```
> 注意：以 `.github/.copilot-config.json` 为工作区绝对规则；`.github/*.json` 为绝对规则；根目录 `*.json` 为项目级，遵循优先级覆盖。

## 消费最终生效规则（calc-effective-rules.json）
- 生成位置：`/.github/logs/calc-effective-rules.json`，由 CI 校验工作流产生。
- 用途：作为“当前项目的最终规则快照”，供脚本或流水线读取。

### 任意路径可识别的落地清单
- 将 `.github/` 整体置于目标项目根目录，无需依赖固定仓库名；`gitc.md` 置于同一根目录。
- 如需外部规则，创建以 `YL`/`yl` 开头的 JSON 文件并与 `.github` 同级；否则保持留空使用内置回退。
- 在 VS Code 打开任意路径的项目时，Copilot 启动即按优先级读取并在失败时自动回退；无需额外配置。
- CI 侧保持 `workflows/validate-copilot-config.yml` 运行，可在新路径照常输出 `.github/logs/calc-effective-rules.json` 供下游消费。

### Shell 示例：读取 include/exclude 并打印
```bash
jq -r '.paths_include_exclude.include[]?' .github/logs/calc-effective-rules.json | sed 's/^/include: /'
jq -r '.paths_include_exclude.exclude[]?' .github/logs/calc-effective-rules.json | sed 's/^/exclude: /'
```

### Python 示例：根据最终规则进行筛选
```python
import json, pathlib
rules = json.load(open('.github/logs/calc-effective-rules.json', 'r', encoding='utf-8'))
inc = rules['paths_include_exclude']['include'] or []
exc = rules['paths_include_exclude']['exclude'] or []
for p in pathlib.Path('.').rglob('*'):
   s = str(p)
   if any([pathlib.PurePath(s).match(glob) for glob in exc]):
      continue
   if inc and not any([pathlib.PurePath(s).match(glob) for glob in inc]):
      continue
   # 在此执行对应的处理逻辑，例如代码检查或构建
   print('process:', s)
```
# GitHub Copilot 配置集成说明

**日期**: 2025-12-13  
**配置版本**: 1.0.0  
**与现有配置的兼容性**: ✅ 完全兼容  
**说明**: 本模板仅包含 `.github/.copilot-config.json` 与文档；文中提到的 `YLAI-AUTO/*`、`Task/ai_recognition_config.py` 等文件在此仓库中不存在，均为示例路径，移植到实际项目时请替换为真实文件。无论 `.github` 上级目录名称为何，一律将 `.github` 的上级目录视为项目根目录；`.github` 目录内的所有 `.json` 配置均需识别并视为 Copilot 绝对规则；根目录下的 `.json` 配置（不限定文件名）仅针对该根目录对应的项目生效且为优先。
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

## 📌 与现有配置的关系

本配置与项目中已有的以下文件**互不冲突，相互补充**：

### 1. `YLAI-AUTO/核心指向.json`
```
关系: 互补
作用:
  - 核心指向.json: 定义项目文件和路径的指向关系
  - .copilot-config.json: 定义 Copilot 的编码规范和分析规则

集成说明:
  ✓ .copilot-config.json 可以识别核心指向.json 的内容
  ✓ Copilot 会根据这些指向进行文件分析
  ✓ 帮助 Copilot 理解文件之间的关联
```

### 2. `YLAI-AUTO/AI定义分析.prompt.yml`
```
关系: 互补
作用:
  - AI定义分析.prompt.yml: 定义项目分析的 Prompt 模板
  - .copilot-config.json: 定义编码规范和优化策略

集成说明:
  ✓ .copilot-config.json 补充了编程语言级别的规则
  ✓ 两者共同指导 Copilot 的行为
  ✓ Prompt 层级高于配置规则
```

### 3. `YLAI-AUTO/function_registry.json`
```
关系: 兼容
作用:
  - function_registry.json: 注册所有可用函数
  - .copilot-config.json: 分析和优化函数实现

集成说明:
  ✓ .copilot-config.json 会自动识别注册的函数
  ✓ 在生成新函数时参考现有注册
  ✓ 确保所有新函数都按规范注册
```

### 4. `Task/ai_recognition_config.py`
```
关系: 兼容
作用:
  - ai_recognition_config.py: Python 识别配置（数据结构）
  - .copilot-config.json: JSON 形式的编码规范

集成说明:
  ✓ 两者都用于 Copilot 指导
  ✓ .copilot-config.json 优先生效
  ✓ ai_recognition_config.py 可作为参考实现
```

---

## 🔄 协同工作流程

### 当 Copilot 处理任务时：

```
1. 读取 .copilot-config.json
   ↓
2. 根据 projectDiscovery 自动扫描项目
   ↓
3. 应用 languageRules 中的编码规范
   ↓
4. 查找 YLAI-AUTO/核心指向.json 确定文件关联
   ↓
5. 检查 YLAI-AUTO/function_registry.json 寻找相似函数
   ↓
6. 应用 codeGenerationRules 的优化策略
   ↓
7. 根据 YLAI-AUTO/AI定义分析.prompt.yml 的 Prompt 调整
   ↓
8. 生成符合所有规范的代码建议
```

---

## ✅ 优势

### 1. **层级化指导**
```
Prompt 层 (最高) ← YLAI-AUTO/AI定义分析.prompt.yml
   ↓
规范层 ← .copilot-config.json
   ↓
注册层 ← YLAI-AUTO/function_registry.json
   ↓
项目指向层 ← YLAI-AUTO/核心指向.json
```

### 2. **自动识别与学习**
```
✓ Copilot 自动学习现有规范
✓ 自动识别项目结构
✓ 自动查找相似代码
✓ 自动适应项目风格
```

### 3. **冗余性与保险**
```
✓ 即使其他配置丢失，.copilot-config.json 仍能工作
✓ 提供独立的、便携的编码规范
✓ 可以复制到任何没有其他配置的项目
```

---

## 📋 配置优先级顺序

当多个配置存在时，按以下优先级应用：

```
1. YLAI-AUTO/AI定义分析.prompt.yml (最高优先级)
   └─ Prompt 层级指导，影响最大

2. .copilot-config.json
   └─ 编码规范和优化策略

3. YLAI-AUTO/核心指向.json
   └─ 文件关联和路径指向

4. YLAI-AUTO/function_registry.json
   └─ 函数注册和可用性

5. Task/ai_recognition_config.py (最低优先级)
   └─ 备用参考实现
```

---

## 🎯 使用场景示例

### 场景 1：添加新 Python 脚本

```
用户请求: "在 scripts/ 目录添加数据验证脚本"

Copilot 的处理流程:
1. ✓ 从 .copilot-config.json 读取 Python 规范
   - 应用 snake_case 命名
   - 4空格缩进
   - Google 风格文档字符串

2. ✓ 检查 scripts/ 目录的现有脚本
   - 识别现有的命名模式
   - 检查导入方式
   - 分析错误处理方式

3. ✓ 查询 function_registry.json
   - 找到相似的验证函数
   - 复用已存在的工具函数
   - 避免重复实现

4. ✓ 应用 AI定义分析.prompt.yml
   - 调整生成风格
   - 添加必要的文档
   - 确保与项目一致

结果: 与现有代码完全一致的新脚本
```

### 场景 2：优化 API 模块

```
用户请求: "优化 backend/api/ 中的用户管理接口"

Copilot 的处理流程:
1. ✓ 扫描 backend/api/ 所有接口
2. ✓ 应用 .copilot-config.json 中的 JavaScript/Python 规范
3. ✓ 查询 核心指向.json 了解 API 路由结构
4. ✓ 检查 function_registry.json 中的现有接口函数
5. ✓ 识别相似接口的模式
6. ✓ 提议优化方案，保持一致性

结果: 优化方案符合所有现有规范
```

---

## 🛠️ 自定义与扩展

### 如何添加新规范

#### 方法 1：修改 .copilot-config.json（推荐）
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

#### 方法 2：更新 AI定义分析.prompt.yml
```yaml
- role: assistant
  content: |
    添加新的规范要求...
```

#### 方法 3：更新 function_registry.json
```json
{
  "new_category": {
    "functions": [...]
  }
}
```

### 优先级建议

| 修改类型 | 修改位置 | 优先级 |
|---------|--------|--------|
| 通用编码规范 | .copilot-config.json | 1️⃣ 推荐 |
| Prompt 指导 | AI定义分析.prompt.yml | 2️⃣ 可选 |
| 函数复用 | function_registry.json | 3️⃣ 可选 |
| 项目结构 | 核心指向.json | 4️⃣ 维护 |

---

## 🔍 故障排除

### 问题 1：配置冲突怎么办？

**解决方案**：
```
按优先级顺序检查：
1. AI定义分析.prompt.yml 中的 Prompt
2. .copilot-config.json 中的规范
3. function_registry.json 中的注册

前面的覆盖后面的
```

### 问题 2：某个规范没有被应用？

**检查清单**：
```
☐ .copilot-config.json 中是否启用了该规范（enabled: true）
☐ 文件是否匹配 filePatterns
☐ 优先级是否足够高
☐ VS Code 是否已重启
```

### 问题 3：与现有配置不兼容？

**解决步骤**：
```
1. 确认现有配置的优先级
2. 在 .copilot-config.json 中调整优先级
3. 或在 AI定义分析.prompt.yml 中添加覆盖规则
4. 测试并验证结果
```

---

## 📊 功能覆盖矩阵

| 功能 | 核心指向.json | AI定义分析.yml | function_registry.json | .copilot-config.json |
|------|--------------|--------------|----------------------|------------------|
| 路径指向 | ✅ | ❌ | ❌ | ❌ |
| Prompt 指导 | ❌ | ✅ | ❌ | ❌ |
| 函数注册 | ❌ | ❌ | ✅ | ❌ |
| 编码规范 | ❌ | ⚠️ | ❌ | ✅ |
| 语言规则 | ❌ | ⚠️ | ❌ | ✅ |
| 项目自动发现 | ❌ | ❌ | ❌ | ✅ |
| 代码复用检测 | ❌ | ❌ | ❌ | ✅ |
| 一致性验证 | ❌ | ⚠️ | ❌ | ✅ |

**图例**: ✅ 完全支持 | ⚠️ 部分支持 | ❌ 不支持

---

## 💡 最佳实践

### ✅ 推荐做法

1. **保持 .copilot-config.json 作为编码规范的单一来源**
   ```
   所有编码规范都在这里定义
   避免在其他地方重复
   ```

2. **使用 AI定义分析.prompt.yml 来指导 Prompt 层**
   ```
   超越编码规范的高级指导
   项目特定的 AI 行为指导
   ```

3. **定期同步所有配置**
   ```
   团队保持配置一致
   定期检查是否有冲突
   ```

4. **在变更前备份配置**
   ```
   git commit 前保存配置
   记录变更理由
   ```

### ❌ 避免做法

1. **不要在多个文件中定义相同的规范**
   ```
   容易导致冲突
   难以维护一致性
   ```

2. **不要依赖隐含的优先级**
   ```
   明确文档化优先级
   在注释中说明原因
   ```

3. **不要忽视现有配置**
   ```
   理解现有设置的目的
   检查兼容性
   ```

---

## 📚 相关文档

- `COPILOT_CONFIG_GUIDE.md` - 详细的配置指南
- `COPILOT_QUICK_START.md` - 快速参考手册
- `YLAI-AUTO/AI定义分析.prompt.yml` - Prompt 模板
- `YLAI-AUTO/核心指向.json` - 项目文件指向
- `YLAI-AUTO/function_registry.json` - 函数注册表

---

## 🚀 后续步骤

1. **验证集成**
   ```bash
   # 检查所有配置文件
   ls -la .copilot-config.json
   ls -la YLAI-AUTO/AI定义分析.prompt.yml
   ```

2. **在 Copilot Chat 中测试**
   ```
   @workspace 告诉我你识别到的所有配置
   ```

3. **定期维护**
   ```
   ☐ 每周检查配置一致性
   ☐ 每月更新规则
   ☐ 每季度进行一次全面审查
   ```

---

**版本**: 1.0.0  
**最后更新**: 2025-12-13  
**状态**: ✅ 生产就绪
