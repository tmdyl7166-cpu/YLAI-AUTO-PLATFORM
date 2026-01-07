# GitHub Copilot 配置模板 - 完全可移植封装

## 封装验证状态
✅ **已按“外部校验失败即回退内置规则”策略校验**  
✅ **完全自包含，可移植至任意目录**  
✅ **无硬编码绝对路径依赖**

---

## 核心设计原则

### 1. gitc.md 作为项目绝对规则文档
**设计哲学**: `gitc.md` 是项目的**绝对规则描述文档**，具有最高优先级：
- 可配置 `external_rules_file` 指向外部 `.json` 规则文件
- 未配置外部规则时，使用 gitc.md 自身的描述内容
- `.github/.copilot-config.json` 仅作为默认规则库

### 2. 规则优先级体系
```
优先级 1 (最高): gitc.md 中指定的 external_rules_file（须以 YL/yl 开头、与 .github 同级、JSON 有效）
优先级 2: gitc.md 文档本身的描述内容
优先级 3 (默认/回退绝对规则): .github/.copilot-config.json 内置规则
```

### 3. 上级目录自动识别
**关键规则**：无论 `.github` 文件夹被放置在何处，系统自动将其**上级目录**识别为项目根目录。

示例：
```
/any/path/project-A/.github/  → 项目根 = /any/path/project-A/
/home/user/repos/app/.github/ → 项目根 = /home/user/repos/app/
```

---

## 封装内容清单

### 核心配置文件
- **`gitc.md`** - 项目绝对规则描述文档（最高优先级）
- **`.copilot-config.json`** (691行) - 内置默认规则库，JSON 语法已验证
- **`copilot-instructions.md`** - AI 代理指令集

### 文档文件
- `COPILOT_QUICK_START.md` - 快速上手指南
- `COPILOT_CONFIG_GUIDE.md` - 详细配置说明
- `COPILOT_INTEGRATION_GUIDE.md` - 集成与使用示例
- `COPILOT_CORE_TRIGGERS.md` - 核心触发关键词说明
- `PLACEHOLDER_GUIDE.md` - 占位字段填写指南（新项目必读）
- `PLACEHOLDER_CHECKLIST.md` - 占位字段快速检查清单

### 自动化工作流
- `workflows/validate-copilot-config.yml` - CI 校验与规则计算

### 输出目录（自动生成）
- `logs/` - 日志与规则快照（运行时创建）
  - `calc-effective-rules.json` - 最终生效规则（包含 external_rules_file 信息）
  - `validation.log` - 校验记录
  - `repair.log` - 修复记录

---

## 使用方式

### 方式一：使用 gitc.md 文档描述（推荐）
```markdown
# 在 gitc.md 中不配置 external_rules_file
{
  "external_rules_file": ""
}

→ 系统使用 gitc.md 文档描述 + .github/.copilot-config.json 默认规则
→ 适合大多数项目，直接在 gitc.md 中描述项目规范即可
```

### 方式二：指定外部规则文件（须与 .github 同级且以 YL 开头）
```markdown
# 在 gitc.md 中配置外部规则路径
{
  "external_rules_file": "YL-copilot-rules.json"
}

→ 系统在项目根加载 YL-copilot-rules.json 作为绝对规则（需与 .github 同级、命名以 YL/yl 开头且 JSON 有效）
→ .github/.copilot-config.json 仅提供语言定义等基础信息
```

---

## 移植步骤

### 方式一：整体复制（推荐）
```bash
cp -r /source/path/.github /target/project/

# 必读：查看占位字段填写指南
cat /target/project/.github/PLACEHOLDER_GUIDE.md

# 编辑项目规则文档，填写必填字段
vim /target/project/gitc.md

# 可选：创建外部规则文件（需与 .github 同级且以 YL 开头）
# vim /target/project/YL-copilot-rules.json
```

### 方式二：Git 子模块
```bash
git submodule add <repo-url> .github
# 或使用 subtree
git subtree add --prefix=.github <repo-url> main --squash
```

### 方式三：模板初始化
```bash
git clone <repo-url> new-project
cd new-project
```

---
## 自包含验证清单

### ✅ 路径独立性
- [x] 无 `/home/`、`/Users/` 等绝对路径
- [x] 使用 `.github/` 相对前缀
- [x] 使用 `<root>/` 表示上级目录
- [x] CI 脚本使用相对路径（`python3 -m json.tool .github/.copilot-config.json`）

### ✅ 配置自洽性
- [x] JSON 语法校验通过
- [x] 所有文档引用路径一致
- [x] 优先级逻辑无冲突
- [x] 双向规则明确（gitc.md ↔ .copilot-config.json）

### ✅ 运行时适配
- [x] 根目录自动识别（`.github` 的上级）
- [x] 日志路径自动创建（`.github/logs/`）
- [x] CI 工作流相对路径执行
- [x] 错误修复日志自包含

---

## 核心逻辑保证

### 不变性保证
无论 `.github` 被放置在何处，以下逻辑**始终不变**：

1. **根目录定位**：`.github` 的上级目录 = 项目根
2. **绝对规则**：`.github/` 内容优先级最高
3. **回退机制**：`gitc.md` 留空 → 回退 `.github` 规则

### 冲突消解
- 同优先级内：后声明覆盖先声明
- 跨优先级：高优先级完全覆盖低优先级
- gitc.md 与 .github 冲突：gitc.md 已填写字段优先

---

## 使用示例

### 场景 1：新项目初始化
```bash
mkdir my-new-project
cd my-new-project
git init
cp -r /template/.github .
# 立即可用，无需配置
```

```
### 场景 3：多项目共享
```bash
# 方案 A：符号链接（推荐同一文件系统）
ln -s /shared/copilot-config/.github project-A/.github
ln -s /shared/copilot-config/.github project-B/.github

# 方案 B：独立复制（推荐跨系统/隔离环境）
cp -r /template/.github project-A/
cp -r /template/.github project-B/
```

---

## 校验命令

```bash
# 1. JSON 语法校验
python3 -m json.tool .github/.copilot-config.json

# 2. 规则一致性检查（手动）
grep -r "\.github" .github/ | grep -v "Binary"

# 3. 触发 CI 校验（如果已配置）
git add .github
git commit -m "Add Copilot config"
### CI 自动校验
- 验证 JSON 语法
- 检查占位符完整性
- 确认 gitc.md 存在
## 常见问题
### Q: 移动 .github 后需要重新配置吗？
**A**: 不需要。所有路径自动适配新位置。

### Q: 可以重命名 .github 文件夹吗？
**A**: 运行本目录下的校验命令，确保无错误输出。

### Q: logs/ 目录不存在怎么办？
**A**: 正常现象。首次运行 CI 或触发"整理验证"时自动创建。

---

## 维护说明

### 更新流程
1. 修改 `.github/` 内任意文件
2. 运行 `python3 -m json.tool .github/.copilot-config.json` 验证语法
3. 确认所有文档引用一致
4. 提交变更

### 扩展指南
- 新增语言规则 → 更新 `.copilot-config.json` 的 `languageRules`
- 新增触发关键词 → 更新 `copilot-instructions.md` 与 `COPILOT_CORE_TRIGGERS.md`
- 新增文档 → 放置在 `.github/` 下并更新本 README

---

## 技术规格

- **JSON Schema 版本**: 1.0.0
- **最低 Python 版本**: 3.6+ (用于 json.tool)
- **CI 平台**: GitHub Actions (可适配 GitLab CI / Jenkins)
- **文档格式**: Markdown (GitHub Flavored)
- **字符编码**: UTF-8

---

## 许可与贡献

本配置模板完全可移植且无外部依赖。欢迎：
- 复制到任意项目使用
- 根据需求定制修改
- 反馈问题与改进建议

**最后更新**: 2025-12-13  
**封装验证**: ✅ 通过
