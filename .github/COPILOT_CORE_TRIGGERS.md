# Copilot 核心触发与占位配置

本说明聚焦关键触发关键词与需要设置的核心项，便于快速启用与填写。

执行优先级：
- 1）项目识别一级内容：`<root>/gitc.md`（已填写字段视为项目级绝对规则，优先应用）
- 2）绝对规则：`.github/.copilot-config.json` 与 `.github/*.json`（当 gitc.md 对应字段留空或缺失时回退至此）
- 3）项目根 JSON：`<root>/*.json`（仅作用于该项目根，受上述两者覆盖）

## 核心触发关键词
- `整理验证`：对所有配置与文档执行双向联动的全量识别与验证，确保无冲突、无重复。
  - 触发方式：在需求中出现“整理验证”关键词时自动执行。
  - 报告格式：`checkItem` / `status(pass|warning|fail)` / `location(path:line)` / `suggestedAction`。

- `提出建议`：跨文件/配置/上下文给出结构、性能、安全、可维护性、可移植性、文档等维度的优化建议。
  - 触发方式：在需求中出现“提出建议”关键词时自动执行。
  - 优先级：`must`（影响功能）、`recommended`（最佳实践）、`optional`（锦上添花）。

- `合并`：识别多个配置中相同键的功能唯一性，合并重复内容，统一逻辑并清理冗余。
  - 触发方式：在需求中出现“合并”关键词时自动执行。
  - 行为：热加载、兼容性检查（向下/向上）。

## 必填/可选占位配置
- `/.github/.copilot-config.json`
  - 必填：`metadata.schemaVersion`（已设为 `"1.0.0"`）。
  - 可选：`versionManagement.changelogPath`（默认 `CHANGELOG.md`）。
  - 可选：`errorHandling.logOutputPath`（默认 `/.github/logs/`）。
  - 可选：`communityAndExtensions.pluginMechanism.hooks`（默认启用 `onBeforeScan`/`onAfterOptimize`）。

- `<root>/gitc.md`（项目识别一级内容）
  - 作用域：仅针对除 `.github/` 外的整个项目。
  - 若不存在：自动创建标准模板，包含以下占位项：
    - `project_overview`
    - `copilot_execution_strategy`
    - `language_conventions_overrides`
    - `paths_include_exclude`
    - `optimization_focus`
    - `ci_validation_schemaPath`
    - `custom_hooks_configuration`

- `placeholders`（见 `.github/.copilot-config.json`）
  - 与 `gitc.md` 的字段一一对应：`project_overview`、`copilot_execution_strategy`、`language_conventions_overrides`、`paths_include_exclude(include/exclude)`、`optimization_focus`、`ci_validation_schemaPath`、`custom_hooks_configuration(onBeforeScan/onAfterOptimize)`。
  - 留空策略：gitc.md 留空时回退到 `.github` 绝对规则；填写后作为项目级绝对规则覆盖。

- CI 工作流（可选）
  - `/.github/workflows/validate-copilot-config.yml`：用于在 CI 中校验 JSON 语法与 `jsonschema`。
  - 占位：`schemaPath`（指向 JSON Schema 文件）。

## 快速命令
```bash
# 本地语法校验
python3 -m json.tool .github/.copilot-config.json
```

更多细节请参阅：
- `/.github/COPILOT_QUICK_START.md`
- `/.github/COPILOT_CONFIG_GUIDE.md`
- `/.github/COPILOT_INTEGRATION_GUIDE.md`
