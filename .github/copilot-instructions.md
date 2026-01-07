# Copilot Instructions

- Purpose: portable GitHub Copilot configuration template; no app code or build pipeline.
- Key files: `gitc.md` (absolute project rules document), `.copilot-config.json` (default rules library), `COPILOT_CONFIG_GUIDE.md` (reference), `COPILOT_INTEGRATION_GUIDE.md` (coexistence rules), `COPILOT_QUICK_START.md` (how-to).
- Expected usage: copy `.github/` folder into target project root; `gitc.md` acts as absolute rules document with highest priority; nothing else to install.
- Behavior: `gitc.md` can specify external `.json` rules file or use its own descriptions; `.copilot-config.json` serves as default rules library; unlimited project scan depth, broad language detection, full-project context window, strong bias to reuse existing code before creating new files.
- Configuration priority (VS Code startup): 1) external_rules_file in gitc.md (if exists, starts with YL/yl, same level as .github/), 2) gitc.md document descriptions, 3) .github/.copilot-config.json (default/absolute fallback). Copilot in VS Code always applies this order on workspace load; any外部规则校验失败时立即回退到 `.github/.copilot-config.json` 作为绝对规则。
- External rules file strict requirements: 1) Must be at same level as .github/ folder (project root), 2) Filename must start with YL/yl (case-insensitive), 3) Must be valid JSON format. Validation failure triggers fallback to `.github/.copilot-config.json` as the absolute ruleset and logs the error (E002/E003/E004/E005).
- Language conventions: Python snake_case + 4-space + Google docstrings; JS/TS camelCase + 2-space + double quotes; Java PascalCase + 4-space; Go mixedCase + explicit error handling; Shell snake_case + 2-space + `set -e`; HTML semantic + WCAG 2.1; CSS kebab-case + 2-space.
- Generation priority: reuse > consistency check > deduplicate > create new files only when necessary.
- Content optimization workflow: 先用全局描述复述任务 → 给出精简方案/变更要点 → 待确认后再执行 → 完成后交付全文并询问是否再调。
- 内容整体优化要求: 每次优化需对全量修改内容进行整体逻辑梳理和整理，保持结构不变，仅优化表述与一致性，确保无逻辑冲突。
- 内容优化执行步骤:
	1) 获取任务与全局描述，先用中文复述；包含当前状态摘要（文件数、配置项数、已知问题清单）。
	2) 给出精简方案/变更要点清单，等待确认；包含风险评估（可能影响的功能点）与回滚方案（Git commit/备份路径）。
	3) 执行修改（不改结构，只调表述/一致性），复核逻辑无冲突；明确复核检查点：语法正确性、逻辑一致性、路径有效性、引用完整性。
	4) 提供全文更新结果并询问是否需再调整；附带 diff 摘要（新增/修改/删除行数）与测试验证建议（如运行 JSON 校验命令）。
- 内容联动优化规则: 每次优化需同步审视相关配置与上下文文件，一并优化；优化后检查配置是否重复、指向路径是否正确。
- 自动修复策略: 部署脚本或优化内容后如出现错误，无需询问，自动多维度迭代修复直至任务可正常运行，再反馈结果。
	- 修复轮次上限：最大迭代 5 次，避免无限循环。
	- 修复日志记录：每轮记录【尝试方法】【失败原因】【采用方案】，存储于 `.github/logs/repair.log`。
	- 失败处理机制：达到 5 次上限仍未修复时，终止自动修复，提供详细诊断报告（错误堆栈、已尝试方案、建议人工介入点）并通知用户。
- "整理验证" 关键词: 执行该指令时必须对所有功能与配置进行双向联动的全量识别与验证，绝不遗漏，确保无冲突、无重复；需要：
	1) 覆盖整个项目全部配置（含隐藏目录与全部文件类型，逐行检查）；
	2) 双向检查：配置指向与被指向的文件/路径均需匹配且无缺失；
	3) 冲突/重复判定：相同键/路径/规则出现冲突或重复时给出消解方案；
	4) 输出完整报告：列出检查范围、发现项、修复动作与剩余风险。
	- 检查范围明细：覆盖所有文件类型（`.md`、`.json`、`.yml`、`.sh`、`.py`、`.js`、`.ts` 等，不限类型）。
	- 双向检查示例：配置A引用路径B时，需验证B存在且内容符合A的预期（如 `.copilot-config.json` 引用 `languageRules` 时，验证对应语言文件确实存在）。
	- 冲突消解策略：`gitc.md 中 external_rules_file`（最高） > `gitc.md 文档描述`（次高） > `.github/.copilot-config.json`（默认库）；相同键以高优先级覆盖。
	- 报告输出格式：结构化输出包含【检查项】【状态：通过/警告/失败】【位置：文件路径+行号】【建议动作】。
- "提出建议" 关键词: 触发时需基于全局内容联动提出多维度扩展性优化建议，覆盖跨文件/配置/上下文的改进点，保持一致性、可移植性、无冲突、无重复。
	- 建议分类维度：【结构优化】【性能提升】【安全加固】【可维护性】【可移植性】【文档完善】等。
	- 优先级标注：每条建议标注为"必须"（影响功能）、"推荐"（最佳实践）、"可选"（锦上添花）三级。
	- 影响范围评估：说明影响哪些文件/配置（如"影响 `gitc.md` 与所有 `.md` 文档"）。
	- 实施成本估算：标注改动复杂度为【低】（单文件小改）、【中】（多文件协调）、【高】（架构级调整）。
- 中文优先: 解释与沟通优先使用中文自然语言。
- 根目录定位: 无论 `.github` 上级目录名称为何，默认将其上级目录视为项目根。
- 项目绝对规则文档: `<root>/gitc.md` 为项目绝对规则描述文档，优先级最高；可配置 `external_rules_file` 指向外部 `.json` 规则文件；未配置时使用 gitc.md 描述 + 内置规则。
- 配置解析规则: 优先级顺序为 `gitc.md 中 external_rules_file (如存在)` > `gitc.md 文档描述` > `.github/.copilot-config.json (默认/回退绝对规则)`；VS Code 启动 Copilot 时必然按此顺序解析。
 	- 外部规则文件严格要求：gitc.md 中可配置 `external_rules_file` 字段，必须满足：1) 文件名以 YL/yl 开头（大小写不敏感）；2) 文件与 .github/ 目录处于同一层级（项目根目录）；3) 有效的 JSON 格式。
 	- 规则加载逻辑：如 external_rules_file 已配置且满足所有严格要求，该文件作为项目绝对规则；不满足任一要求（含缺失、命名/路径错误、JSON 无效）则记录错误并**回退到 `.github/.copilot-config.json` 作为绝对规则**；未配置时使用 gitc.md 文档描述。
	- 有效示例：`YL-copilot-rules.json`, `yl_config.json`, `YLrules.json`（均与 .github/ 同级）。
	- 无效示例：`my-rules.json`（未以YL开头）、`config/YL-rules.json`（不在根目录）、`.github/YL.json`（在.github内部）。
		- 冲突消解策略：`gitc.md 中 external_rules_file (满足YL命名且同级)`（最高） > `gitc.md 文档描述`（次高） > `.github/.copilot-config.json`（默认库）；相同键以高优先级覆盖。
	- 内置规则库：`.github/.copilot-config.json` 仅作为默认规则库，提供语言规范、扫描策略等基础定义。
	- 双向联动机制：gitc.md 与 .copilot-config.json 的配置字段双向对应，CI 自动校验一致性并生成最终规则快照至 `.github/logs/calc-effective-rules.json`。
	- "合并" 关键词：触发时对多个配置文件相同键进行功能唯一性识别，合并重复内容，统一逻辑后生成唯一脚本，清理冗余配置。
	- 热加载机制：配置修改后自动刷新并验证，无需手动重启编辑器。
	- 兼容性检查：自动处理不同版本配置文件的向下/向上兼容性，必要时提示升级或降级路径。
- 验证/优化扫描策略: 需验证/优化时，对目标目录及子目录（含隐藏目录）无限深度递归，逐行完整解析所有文件类型，不得摘要、截断或省略。
- 扫描策略增强:
	- 性能优化：大型项目（>10万行代码）采用增量扫描策略，仅扫描变更文件；超大项目可选采样模式。
	- 敏感信息保护：不扫描 `.env`、`.pem`、`.key`、`secrets/` 等敏感路径。
	- 扫描结果缓存：缓存失效条件为文件修改时间或内容 hash 变化；验证逻辑完整且无重复时，仅保留最后 1 次缓存。
- 语言规则扩展:
	- 新增语言：Rust (snake_case + 4-space)、Ruby (snake_case + 2-space)、PHP (camelCase + 4-space)、Swift (camelCase + 4-space)、Kotlin (camelCase + 4-space)。
	- 框架特定规则：React/Vue/Angular (组件化、Hooks 优先)、Django/Flask (MTV 模式、蓝图隔离)、Spring Boot (分层架构、依赖注入)。
	- 跨语言一致性：统一命名规范（接口用 I 前缀、抽象类用 Abstract 前缀）、注释格式（JSDoc/Docstring 风格）、错误处理（统一异常类型与日志格式）。
- Ignore patterns（内置）: `node_modules/`, `.git/`, 虚拟环境, 构建输出 (`dist/`, `build/`, `target/`, 等), 缓存, `*.log`；避免建议修改被忽略路径。
- 外部示例文件说明: 文档中提到的 `YLAI-AUTO/AI定义分析.prompt.yml`、`function_registry.json` 等仅为示例，仓库中不存在，勿假定其存在。
- 项目适配: 如需适配具体项目，优先调整 `languageRules` 的 `filePatterns`/`entryPoints`/`configFiles` 与 `projectDiscovery.patterns`，避免硬编码路径。
- 便携性: 保持 `.copilot-config.json` 通用，避免项目特定绝对路径或环境值，优先使用相对模式。
- JSON 校验: 修改后可运行 `python3 -m json.tool .copilot-config.json` 进行语法校验。
- 文档更新: 更新说明请放入顶层指南文件，避免在 JSON 内嵌注释以保持可机读性。
- 测试/构建: 本仓库无测试/构建任务，验证仅需 JSON 语法检查。
- 错误处理与日志:
	- 错误分级：【致命】立即终止并报警；【警告】记录日志继续执行；【提示】仅显示建议。
	- 日志输出位置：默认 `.github/logs/`，可通过环境变量自定义。
	- 错误码体系：E001（配置冲突）、E002（路径不存在）、E003（语法错误）、W001（性能警告）、I001（优化建议）。
- 测试与验证机制:
	- 配置自检工具：提供 `python3 -m json.tool .github/.copilot-config.json` 进行语法校验；推荐集成 `jsonschema` 验证。
	- 集成测试：在 CI/CD 中添加配置验证步骤（如 GitHub Actions workflow）。
	- 示例项目：提供单体应用（Python Django）、微服务（Go + Docker）、全栈（React + Node.js）三种典型配置示例。
- 文档与示例:
	- 快速诊断指南：常见问题流程图（配置不生效 → 检查路径 → 验证语法 → 重启编辑器）。
	- 迁移指南：从 `.cursorrules` / `.windsurfrules` 迁移到本配置的字段映射表与自动转换脚本。
	- 视频教程索引：链接官方文档 https://aka.ms/vscode-instructions-docs 与社区教程。
- 版本管理:
	- 配置版本号：在 `metadata` 中增加 `schemaVersion: "1.0.0"` 字段，便于未来升级检测。
	- 变更日志：维护 `CHANGELOG.md` 记录每个版本的【新增】【变更】【弃用】【修复】。
	- 弃用策略：旧版本字段保留 2 个大版本周期（约 6 个月），提供迁移脚本与警告提示。
- 社区与扩展:
	- 插件机制：支持用户在 `customRules` 字段自定义规则或钩子函数（如 `onBeforeScan`、`onAfterOptimize`）。
	- 贡献指南：通过 Pull Request 向 `languageRules` 贡献新语言/框架，需包含测试用例与文档。
	- 反馈渠道：GitHub Issues 报告问题，Discussions 参与讨论，提供模板加速响应。
- 新语言/规则: 新增语言或规则时遵循现有结构：`enabled`/`priority`/`filePatterns`/`conventions`/`analysisRules`。
- 避免泛化: 不给出与本配置无关的通用 Copilot 建议。
- 补充信息: 缺少项目特定要素（框架、入口、目录）时，应先询问再收紧模式。
