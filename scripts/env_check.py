import sys
import subprocess
import shutil

INSTALL_HINTS = {
    'python': 'sudo apt install -y python3.12 python3.12-venv python3.12-dev',
    'node': 'curl -fsSL https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash && nvm install 20 && nvm use 20',
    'dotnet': 'wget https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb && sudo dpkg -i packages-microsoft-prod.deb && sudo apt-get update && sudo apt-get install -y dotnet-sdk-8.0',
    'fastapi': 'python3.12 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip && pip install fastapi uvicorn',
    'docker': 'curl -fsSL https://get.docker.com | sh && sudo systemctl enable docker && sudo systemctl start docker && sudo usermod -aG docker $USER',
}

def check_python():
    try:
        import platform
        v = sys.version_info
        print(f"Python: {platform.python_version()} (major={v.major}, minor={v.minor})")
        assert v.major == 3 and v.minor >= 10, "Python 3.10+ required"
        return True
    except Exception as e:
        print(f"Python check failed: {e}")
        print(f"安装命令: {INSTALL_HINTS['python']}")
        return False

def check_node():
    try:
        out = subprocess.check_output(["node", "--version"], text=True).strip()
        print(f"Node.js: {out}")
        assert out.startswith('v20'), "Node.js 20 LTS required"
        return True
    except Exception as e:
        print(f"Node.js check failed: {e}")
        print(f"安装命令: {INSTALL_HINTS['node']}")
        return False

def check_dotnet():
    try:
        out = subprocess.check_output(["dotnet", "--version"], text=True).strip()
        print(f".NET: {out}")
        assert out.startswith('8'), ".NET 8 LTS required"
        return True
    except Exception as e:
        print(f".NET check failed: {e}")
        print(f"安装命令: {INSTALL_HINTS['dotnet']}")
        return False

def check_fastapi():
    try:
        import fastapi
        print(f"FastAPI: {fastapi.__version__}")
        return True
    except Exception as e:
        print(f"FastAPI check failed: {e}")
        print(f"安装命令: {INSTALL_HINTS['fastapi']}")
        return False

def check_docker():
    try:
        out = subprocess.check_output(["docker", "--version"], text=True).strip()
        print(f"Docker: {out}")
        return True
    except Exception as e:
        print(f"Docker check failed: {e}")
        print(f"安装命令: {INSTALL_HINTS['docker']}")
        return False

def main():
    print("=== 环境自动检测 ===")
    ok = True
    ok &= check_python()
    ok &= check_node()
    ok &= check_dotnet()
    ok &= check_fastapi()
    ok &= check_docker()
    if ok:
        print("\n✅ 所有环境检测通过！")
    else:
        print("\n❌ 有环境未通过，请按上方命令修复。")

if __name__ == "__main__":
    main()
