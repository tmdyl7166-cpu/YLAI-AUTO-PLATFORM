#!/bin/bash
# YLAI-AUTO-PLATFORM GitHub 自动推送脚本

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║       🚀 YLAI-AUTO-PLATFORM GitHub 自动推送脚本 🚀           ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 检查是否在正确的目录
if [ ! -f "pyproject.toml" ]; then
    echo "❌ 错误: 请在项目根目录运行此脚本"
    exit 1
fi

echo "📝 第 1 步: 检查 Git 状态..."
git status
echo ""

echo "📚 第 2 步: 配置 Git 用户信息（如需要）"
read -p "是否需要配置 Git 用户名和邮箱? (y/n, 默认 n): " configure_git
if [ "$configure_git" = "y" ]; then
    read -p "输入 Git 用户名: " git_name
    read -p "输入 Git 邮箱: " git_email
    git config --global user.name "$git_name"
    git config --global user.email "$git_email"
    echo "✅ Git 配置完成"
fi
echo ""

echo "🔗 第 3 步: 配置 GitHub 远程仓库"
echo ""
echo "请选择认证方式:"
echo "  1) HTTPS (快速，需要 Personal Access Token)"
echo "  2) SSH (安全，需要提前生成密钥)"
read -p "选择 (1 或 2): " auth_choice

if [ "$auth_choice" = "1" ]; then
    echo ""
    echo "📋 HTTPS 认证步骤:"
    echo "  1. 打开: https://github.com/settings/tokens"
    echo "  2. 点击 'Generate new token (classic)'"
    echo "  3. 勾选 'repo' 权限"
    echo "  4. 生成 token 并复制"
    echo ""
    read -p "是否已生成 token? (y/n): " token_ready
    
    if [ "$token_ready" = "y" ]; then
        read -p "输入你的 GitHub 用户名: " github_user
        GITHUB_URL="https://github.com/${github_user}/YLAI-AUTO-PLATFORM.git"
        echo ""
        echo "ℹ️  GitHub 仓库 URL: $GITHUB_URL"
        echo ""
        read -p "此 URL 正确吗? (y/n): " url_correct
        
        if [ "$url_correct" = "y" ]; then
            git remote remove origin 2>/dev/null || true
            git remote add origin "$GITHUB_URL"
            echo "✅ 远程仓库已配置"
        else
            read -p "请输入正确的 GitHub 仓库 URL: " GITHUB_URL
            git remote remove origin 2>/dev/null || true
            git remote add origin "$GITHUB_URL"
            echo "✅ 远程仓库已配置"
        fi
    fi

elif [ "$auth_choice" = "2" ]; then
    echo ""
    echo "🔐 SSH 认证步骤:"
    echo "  1. 运行: ssh-keygen -t ed25519 -C 'your-email@example.com'"
    echo "  2. 打开: https://github.com/settings/ssh/new"
    echo "  3. 复制 ~/.ssh/id_ed25519.pub 的内容到 GitHub"
    echo "  4. 添加 SSH 密钥"
    echo ""
    
    if [ ! -f "$HOME/.ssh/id_ed25519.pub" ]; then
        read -p "未找到 SSH 密钥，是否现在生成? (y/n): " generate_ssh
        if [ "$generate_ssh" = "y" ]; then
            read -p "输入 email (用于标识密钥): " ssh_email
            ssh-keygen -t ed25519 -C "$ssh_email" -N "" -f "$HOME/.ssh/id_ed25519"
            echo ""
            echo "✅ SSH 密钥已生成"
            echo "📋 请复制下面的公钥到 GitHub:"
            echo "---"
            cat "$HOME/.ssh/id_ed25519.pub"
            echo "---"
            echo ""
            echo "打开: https://github.com/settings/ssh/new"
            read -p "已添加公钥到 GitHub? (y/n): " ssh_added
        fi
    else
        echo "✅ 找到已有的 SSH 密钥"
    fi
    
    read -p "输入你的 GitHub 用户名: " github_user
    GITHUB_URL="git@github.com:${github_user}/YLAI-AUTO-PLATFORM.git"
    echo ""
    echo "ℹ️  GitHub 仓库 URL: $GITHUB_URL"
    echo ""
    read -p "此 URL 正确吗? (y/n): " url_correct
    
    if [ "$url_correct" = "y" ]; then
        git remote remove origin 2>/dev/null || true
        git remote add origin "$GITHUB_URL"
        echo "✅ 远程仓库已配置"
    else
        read -p "请输入正确的 GitHub 仓库 URL: " GITHUB_URL
        git remote remove origin 2>/dev/null || true
        git remote add origin "$GITHUB_URL"
        echo "✅ 远程仓库已配置"
    fi
else
    echo "❌ 无效选择"
    exit 1
fi

echo ""
echo "🚀 第 4 步: 推送代码到 GitHub..."
echo ""

if [ "$auth_choice" = "1" ]; then
    echo "📝 提示: 当提示输入密码时，请粘贴你的 Personal Access Token (而不是 GitHub 密码)"
    echo ""
fi

echo "执行推送..."
git push -u origin main

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ✅ 推送完成！                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# 验证推送
if git rev-parse origin/main > /dev/null 2>&1; then
    echo "✅ 验证成功: 远程分支已更新"
    echo ""
    echo "📍 仓库地址:"
    git remote -v | grep origin
    echo ""
    echo "🎉 访问你的仓库: $GITHUB_URL"
else
    echo "⚠️  推送可能失败，请检查错误信息"
    exit 1
fi

echo ""
echo "🎯 下一步:"
echo "  1. 打开 https://github.com/yourname/YLAI-AUTO-PLATFORM"
echo "  2. 邀请团队成员"
echo "  3. 配置 Branch Protection 规则"
echo "  4. 启用 GitHub Pages (可选)"
echo ""
echo "✨ 完成！项目已成功上传到 GitHub！"
