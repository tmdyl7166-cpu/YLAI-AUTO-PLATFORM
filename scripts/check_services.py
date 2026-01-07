#!/usr/bin/env python3
"""
服务健康检查脚本
检查前后端服务是否正确运行在0.0.0.0上
"""

import requests
import sys
from typing import List

def check_service(url: str, name: str) -> bool:
    """检查单个服务"""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ {name}: {url} - 正常")
            return True
        else:
            print(f"❌ {name}: {url} - 状态码 {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ {name}: {url} - 连接失败: {e}")
        return False

def main():
    """主检查函数"""
    print("🔍 检查服务健康状态...")

    services = [
        ("http://0.0.0.0:8001/health", "后端API"),
        ("http://0.0.0.0:3001/pages/index.html", "前端主页"),
        ("http://127.0.0.1:8001/health", "后端API(127.0.0.1)"),
        ("http://127.0.0.1:3001/pages/index.html", "前端主页(127.0.0.1)"),
        ("http://localhost:8001/health", "后端API(localhost)"),
        ("http://localhost:3001/pages/index.html", "前端主页(localhost)"),
    ]

    all_ok = True
    for url, name in services:
        if not check_service(url, name):
            all_ok = False

    print()
    if all_ok:
        print("🎉 所有服务检查通过！")
        return 0
    else:
        print("⚠️  部分服务检查失败，请检查配置")
        return 1

if __name__ == "__main__":
    sys.exit(main())
