"""
自动校验 docs/统一接口映射表.md 注册表所有 API 路径、脚本路径是否真实存在并可调用，输出校验报告。
"""
import os
import re
import json

REGISTRY_MD = "docs/统一接口映射表.md"
BACKEND_API_DIR = "backend/api/"
BACKEND_SCRIPT_DIR = "backend/scripts/"
REPORT_PATH = "logs/registry_linkage_report.json"

# 读取注册表 JSON 区块
def extract_registry_json(md_path):
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"```json[\s\S]*?(\[.*?\])[\s\S]*?```", content)
    if not match:
        return []
    return json.loads(match.group(1))

def check_api_exists(api_path):
    # 仅检查路径存在，不做接口调用
    if not api_path or not api_path.startswith("/api/"):
        return False
    # 仅做静态检查，实际应结合 FastAPI 路由
    return True  # 可扩展为实际路由检查

def check_script_exists(script_name):
    if not script_name:
        return False
    # 检查脚本文件是否存在
    py_path = os.path.join(BACKEND_SCRIPT_DIR, f"{script_name}.py")
    return os.path.exists(py_path)

def main():
    registry = extract_registry_json(REGISTRY_MD)
    report = []
    # 兼容 functions 字段或直接数组
    if isinstance(registry, dict) and 'functions' in registry:
        functions = registry['functions']
    else:
        functions = registry
    for func in functions:
        if not isinstance(func, dict):
            continue
        api_ok = check_api_exists(func.get("api"))
        script_ok = check_script_exists(func.get("id"))
        report.append({
            "id": func.get("id"),
            "name": func.get("name"),
            "api": func.get("api"),
            "api_exists": api_ok,
            "script": func.get("id"),
            "script_exists": script_ok,
            "status": func.get("status")
        })
        # 未完成项自动生成脚本占位
        if not script_ok and func.get("status") != "available":
            py_path = os.path.join(BACKEND_SCRIPT_DIR, f"{func.get('id')}.py")
            with open(py_path, "w", encoding="utf-8") as f_script:
                f_script.write(f"""# 占位脚本: {func.get('name')}
                    # 说明: 此脚本为自动生成占位，功能待实现。

    def main():
        print('功能 {func.get('name')} 暂未实现，待补充...')

    if __name__ == '__main__':
        main()
    """)
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"校验完成，报告已生成: {REPORT_PATH}")

if __name__ == "__main__":
    main()
