# GitHub 推送指南

本文档说明如何将本地仓库推送到 GitHub。

## 前置条件

✅ **已完成**:
- ✅ 本地 Git 仓库已初始化
- ✅ 所有代码文件已暂存（621 个文件，74MB）
- ✅ 初始提交已完成 (`05d0fde62`)
- ✅ `.gitignore` 已配置（排除 node_modules, .venv, logs 等）

## 第 1 步：在 GitHub 上创建仓库

### 方法 A：使用 GitHub Web UI（推荐）

1. **打开 GitHub**: https://github.com/new
2. **填写仓库信息**:
   - Repository name: `YLAI-AUTO-PLATFORM`
   - Description: `极限自动化渗透测试平台 - 以 AI 驱动的企业级安全自动化框架`
   - Visibility: `Public` （或 `Private` 如果是私有项目）
   - **不勾选** "Initialize this repository with: ..."（因为我们已有本地提交）
3. **点击** "Create repository"
4. **记录** HTTPS URL（形如 `https://github.com/yourusername/YLAI-AUTO-PLATFORM.git`）

### 方法 B：使用 GitHub CLI（如已安装）

```bash
gh repo create YLAI-AUTO-PLATFORM \
  --public \
  --source=. \
  --remote=origin \
  --push
```

---

## 第 2 步：配置远程仓库并推送

### 2.1 添加远程仓库

将 `<REPO_URL>` 替换为你在 GitHub 创建的仓库 URL（例如：`https://github.com/yourname/YLAI-AUTO-PLATFORM.git`）

```bash
cd /home/xiedaima/桌面/OOO/YLAI-AUTO-PLATFORM

# 检查现有远程（应该没有）
git remote -v

# 添加 GitHub 作为远程源
git remote add origin <REPO_URL>
# 例如：git remote add origin https://github.com/yourname/YLAI-AUTO-PLATFORM.git
```

### 2.2 推送到 GitHub

```bash
# 推送 main 分支及所有提交历史
git push -u origin main

# 输出示例:
# Enumerating objects: 621, done.
# Counting objects: 100% (621/621), done.
# ...
# To https://github.com/yourname/YLAI-AUTO-PLATFORM.git
#  * [new branch]      main -> main
# Branch 'main' set to track remote branch 'main' from 'origin'.
```

### 2.3 验证推送成功

```bash
# 检查远程追踪状态
git status
# 预期输出: On branch main, Your branch is up to date with 'origin/main'.

# 查看远程信息
git remote -v
# 预期输出:
# origin  https://github.com/yourname/YLAI-AUTO-PLATFORM.git (fetch)
# origin  https://github.com/yourname/YLAI-AUTO-PLATFORM.git (push)
```

---

## 第 3 步：验证 GitHub 仓库

1. **打开 GitHub**: https://github.com/yourname/YLAI-AUTO-PLATFORM
2. **检查以下内容**:
   - ✅ 621 个文件已上传
   - ✅ 初始提交可见
   - ✅ 主分支标记为 `main`
   - ✅ `.gitignore` 已应用（node_modules 等不可见）
   - ✅ README.md 自动显示

---

## 故障排除

### 问题 1: "远程仓库已存在"
```bash
# 如果出现错误：fatal: remote origin already exists
git remote remove origin
git remote add origin <NEW_URL>
```

### 问题 2: 认证失败（HTTPS）
如果出现认证错误，请使用 GitHub Personal Access Token：

```bash
# 生成 token: https://github.com/settings/tokens
# 创建新 token，勾选 'repo' 权限

# 使用 token 进行认证（临时方案）
git push -u origin main
# 输入用户名时，按 Enter
# 输入密码时，粘贴 Personal Access Token

# 永久保存 token（安全起见，建议使用 SSH）
git config --global credential.helper store
```

### 问题 3: 使用 SSH 认证（推荐）

1. **生成 SSH 密钥**（如未生成）:
   ```bash
   ssh-keygen -t ed25519 -C "dev@ylai.auto"
   # 或旧版: ssh-keygen -t rsa -b 4096 -C "dev@ylai.auto"
   ```

2. **添加公钥到 GitHub**:
   - 复制公钥: `cat ~/.ssh/id_ed25519.pub`
   - 打开: https://github.com/settings/ssh/new
   - 粘贴公钥，保存

3. **更新远程 URL 为 SSH 格式**:
   ```bash
   git remote set-url origin git@github.com:yourname/YLAI-AUTO-PLATFORM.git
   ```

4. **重新推送**:
   ```bash
   git push -u origin main
   ```

---

## 推送后的后续步骤

### 1. 配置 GitHub Actions（可选）
已包含的 CI 配置：
- `.github/workflows/validate-copilot-config.yml` - 自动验证 Copilot 配置

### 2. 启用 GitHub Pages（可选）
如需在线文档：
```bash
# 在仓库设置中启用 GitHub Pages
# Source: main branch /docs folder
```

### 3. 设置 Branch Protection（推荐）
为主分支添加保护规则：
- 要求 PR 审查
- 要求状态检查通过
- 禁止强制推送

### 4. 创建 Release（可选）
标记第一个版本：
```bash
git tag -a v1.0.0 -m "Initial release: Project structure complete"
git push origin v1.0.0
```

---

## 常见工作流

### 更新代码后推送
```bash
# 查看更改
git status

# 暂存更改
git add .

# 提交
git commit -m "[feature] 添加新功能"

# 推送
git push origin main
```

### 创建特性分支
```bash
# 创建并切换到新分支
git checkout -b feature/amazing-feature

# 修改代码...

# 推送分支
git push -u origin feature/amazing-feature

# 在 GitHub 上创建 Pull Request
```

---

## 参考资源

- [GitHub 帮助 - 关于 Git](https://docs.github.com/zh/get-started/using-git)
- [GitHub 帮助 - 推送提交](https://docs.github.com/zh/get-started/using-git/pushing-commits-to-a-remote-repository)
- [GitHub SSH 密钥设置](https://docs.github.com/zh/authentication/connecting-to-github-with-ssh)

---

## 快速命令总结

```bash
# 一键配置并推送（替换 <REPO_URL>）
cd /home/xiedaima/桌面/OOO/YLAI-AUTO-PLATFORM
git remote add origin <REPO_URL>
git push -u origin main

# 验证
git remote -v
git branch -vv
```

---

**完成后，你的项目将在 GitHub 上可见，其他开发者可以克隆或贡献！** 🎉
