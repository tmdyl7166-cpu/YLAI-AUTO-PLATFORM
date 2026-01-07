# 快速推送命令速查表

## 🚀 一键推送（复制粘贴）

```bash
# 第 1 步：导航到项目目录
cd /home/xiedaima/桌面/OOO/YLAI-AUTO-PLATFORM

# 第 2 步：检查 Git 状态
git status
git log --oneline | head -5

# 第 3 步：配置远程仓库（替换 YOUR_GITHUB_URL）
git remote add origin https://github.com/yourname/YLAI-AUTO-PLATFORM.git

# 第 4 步：推送到 GitHub
git push -u origin main

# 第 5 步：验证成功
git remote -v
git branch -vv
```

## 📋 前置步骤

### 在 GitHub 上创建仓库

```
1. 打开: https://github.com/new
2. Repository name: YLAI-AUTO-PLATFORM
3. Description: 极限自动化渗透测试平台 - 以 AI 驱动的企业级安全自动化框架
4. Visibility: Public (or Private)
5. ❌ 不勾选 "Initialize this repository with:"
6. 点击 "Create repository"
7. 复制仓库 URL
```

## 🔐 认证选项

### 选项 A: HTTPS + Personal Access Token（快速）

```bash
# 1. 在 https://github.com/settings/tokens 创建 token
#    - 勾选 "repo" 权限
#    - 复制 token

# 2. 推送时，输入：
#    用户名: 你的 GitHub 用户名
#    密码: 粘贴 Personal Access Token

git push -u origin main

# 3. (可选) 保存凭证以避免重复输入
git config --global credential.helper store
```

### 选项 B: SSH（推荐）

```bash
# 1. 生成 SSH 密钥（如未生成）
ssh-keygen -t ed25519 -C "dev@ylai.auto"
# 按 Enter 使用默认路径
# 设置 passphrase (可选)

# 2. 复制公钥
cat ~/.ssh/id_ed25519.pub

# 3. 在 GitHub 添加公钥
#    https://github.com/settings/ssh/new
#    粘贴公钥，点击 "Add SSH key"

# 4. 测试 SSH 连接
ssh -T git@github.com

# 5. 添加远程仓库（使用 SSH URL）
git remote add origin git@github.com:yourname/YLAI-AUTO-PLATFORM.git

# 6. 推送
git push -u origin main
```

## ✅ 验证推送成功

```bash
# 本地验证
git log --oneline origin/main  # 显示远程提交
git branch -vv                  # 显示分支跟踪状态
git remote -v                   # 显示远程配置

# GitHub Web 验证
# 打开: https://github.com/yourname/YLAI-AUTO-PLATFORM
# 确认: ✅ 621 个文件
#       ✅ 2 个提交
#       ✅ main 分支
#       ✅ GITHUB_PUSH_GUIDE.md 文件可见
```

## 🔧 常见问题快速解决

### 问题: "fatal: remote origin already exists"

```bash
git remote remove origin
git remote add origin <NEW_URL>
git push -u origin main
```

### 问题: 认证失败

```bash
# HTTPS: 使用 Personal Access Token（不是密码）
# SSH: 检查密钥是否添加到 ssh-agent
ssh-add ~/.ssh/id_ed25519

# 或重新生成密钥
ssh-keygen -t ed25519 -C "dev@ylai.auto"
```

### 问题: 改变远程 URL

```bash
# 从 HTTPS 改为 SSH
git remote set-url origin git@github.com:yourname/YLAI-AUTO-PLATFORM.git

# 验证
git remote -v
```

### 问题: 忘记添加远程

```bash
# 查看现有远程
git remote -v

# 如果为空，添加：
git remote add origin <URL>

# 推送
git push -u origin main
```

## 📚 完整步骤（从头开始）

```bash
#!/bin/bash
set -e

# 导航
cd /home/xiedaima/桌面/OOO/YLAI-AUTO-PLATFORM

# 验证 Git 仓库
echo "=== Git Status ==="
git status

# 显示最近提交
echo "=== Recent Commits ==="
git log --oneline | head -3

# 配置远程（替换 URL）
GITHUB_URL="https://github.com/yourname/YLAI-AUTO-PLATFORM.git"
echo "=== Adding Remote: $GITHUB_URL ==="
git remote add origin "$GITHUB_URL" || git remote set-url origin "$GITHUB_URL"

# 推送
echo "=== Pushing to GitHub ==="
git push -u origin main

# 验证
echo "=== Verification ==="
git log --oneline origin/main | head -3
git branch -vv

echo "✅ 推送完成！"
echo "访问: https://github.com/yourname/YLAI-AUTO-PLATFORM"
```

保存为 `push.sh`，运行：
```bash
chmod +x push.sh
./push.sh
```

## 🎯 推送后的后续步骤

```bash
# 1. 创建和推送新的开发分支
git checkout -b develop
git push -u origin develop

# 2. 标记版本
git tag -a v1.0.0 -m "Initial release: Project structure complete"
git push origin v1.0.0

# 3. 创建特性分支（日常工作）
git checkout -b feature/my-feature
git commit -am "[feature] 添加新功能"
git push -u origin feature/my-feature
# 在 GitHub 上创建 Pull Request

# 4. 更新代码（日常提交）
git add .
git commit -m "[fix] 修复 bug"
git push
```

## 📞 支持

详细指南: 📖 [GITHUB_PUSH_GUIDE.md](GITHUB_PUSH_GUIDE.md)

---

**关键点:**
- ✅ 项目已准备好上传
- 📝 621 个文件，2 个提交
- 🚀 3 步即可推送到 GitHub
- 🔐 选择 HTTPS 或 SSH 认证
- ✨ 完整文档和故障排除指南
