#!/usr/bin/env python3
"""
前后端映射一致性检查脚本
验证前端组件与后端API的映射关系
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Set, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def scan_frontend_components() -> Dict[str, Dict[str, Any]]:
    """扫描前端组件"""
    components_dir = project_root / "frontend" / "static" / "js" / "components"
    components = {}

    print(f"扫描前端组件目录: {components_dir}")
    if not components_dir.exists():
        print(f"组件目录不存在: {components_dir}")
        return components

    vue_files = list(components_dir.glob("*.vue"))
    print(f"发现 {len(vue_files)} 个Vue文件: {[f.name for f in vue_files]}")

    for file_path in vue_files:
        if file_path.name == "Home.vue":
            continue  # 跳过首页组件

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取组件信息
            component_name = file_path.stem
            api_endpoints = extract_api_endpoints(content)
            script_calls = extract_script_calls(content)

            components[component_name] = {
                "file": str(file_path.relative_to(project_root)),
                "api_endpoints": api_endpoints,
                "script_calls": script_calls
            }

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return components

def extract_api_endpoints(content: str) -> List[str]:
    """从Vue组件中提取API端点"""
    endpoints = []

    # 匹配fetch调用中的URL
    fetch_pattern = r'fetch\s*\(\s*["\']([^"\']+)["\']'
    fetch_matches = re.findall(fetch_pattern, content, re.IGNORECASE)
    for match in fetch_matches:
        if match.startswith('/api/'):
            endpoints.append(match)

    # 匹配axios调用
    axios_patterns = [
        r'axios\.(get|post|put|delete)\s*\(\s*["\']([^"\']+)["\']',
        r'axios\s*\(\s*\{\s*[^}]*?url\s*:\s*["\']([^"\']+)["\']',
    ]
    for pattern in axios_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                url = match[1] if len(match) > 1 else match[0]
            else:
                url = match
            if url.startswith('/api/'):
                endpoints.append(url)

    # 去重
    return list(set(endpoints))

def extract_script_calls(content: str) -> List[str]:
    """从Vue组件中提取脚本调用"""
    scripts = []

    # 匹配脚本调用
    patterns = [
        r'kernel\.run\(["\']([^"\']+)["\']',
        r'script["\']\s*:\s*["\']([^"\']+)["\']',
        r'script:\s*["\']([^"\']+)["\']'
    ]

    for pattern in patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        scripts.extend(matches)

    return list(set(scripts))

def scan_backend_apis() -> Dict[str, Dict[str, Any]]:
    """扫描后端API"""
    apis = {}

    # 扫描API路由文件
    api_dir = project_root / "backend" / "api"
    print(f"扫描后端API目录: {api_dir}")
    if not api_dir.exists():
        print(f"API目录不存在: {api_dir}")
        return apis

    py_files = list(api_dir.glob("*.py"))
    print(f"发现 {len(py_files)} 个Python文件: {[f.name for f in py_files]}")

    for file_path in py_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取路由信息
            routes = extract_routes(content)
            print(f"文件 {file_path.name} 中发现 {len(routes)} 个路由")
            for route in routes:
                apis[route["path"]] = {
                    "file": str(file_path.relative_to(project_root)),
                    "method": route["method"],
                    "function": route["function"]
                }

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return apis

def extract_routes(content: str) -> List[Dict[str, Any]]:
    """从Python文件中提取路由"""
    routes = []

    # 匹配FastAPI路由装饰器 - 更精确的模式
    pattern = r'@(?:router|app)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']'
    matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)

    print(f"找到路由匹配: {matches}")

    for method, path in matches:
        # 查找对应的函数名 - 在装饰器后查找def
        start_pos = content.find(f'"{path}"')
        if start_pos == -1:
            start_pos = content.find(f"'{path}'")

        if start_pos != -1:
            # 从路径字符串后开始查找def
            remaining_content = content[start_pos:]
            func_match = re.search(r'def\s+(\w+)\s*\(', remaining_content)
            func_name = func_match.group(1) if func_match else "unknown"
        else:
            func_name = "unknown"

        routes.append({
            "method": method.upper(),
            "path": path,
            "function": func_name
        })

    return routes

def load_script_registry() -> Dict[str, Any]:
    """加载脚本注册表"""
    registry_file = project_root / "function_registry.json"
    yl_file = project_root / "YL-copilot-rules.json"

    if registry_file.exists():
        try:
            with open(registry_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading registry: {e}")
            return {}

    # 回退到 YL-copilot-rules.json 中的 functionRegistry 字段
    if yl_file.exists():
        try:
            with open(yl_file, 'r', encoding='utf-8') as f:
                yl = json.load(f)
            return yl.get("functionRegistry", {})
        except Exception as e:
            print(f"Error loading registry from YL-copilot-rules.json: {e}")
            return {}

    return {}

def validate_mapping(frontend_components: Dict, backend_apis: Dict, script_registry: Dict) -> Dict[str, Any]:
    """验证映射一致性"""
    issues = []
    warnings = []

    # 检查前端组件使用的API是否存在
    for component_name, component_info in frontend_components.items():
        for endpoint in component_info["api_endpoints"]:
            if endpoint not in backend_apis:
                issues.append({
                    "type": "missing_api",
                    "component": component_name,
                    "endpoint": endpoint,
                    "message": f"前端组件 {component_name} 使用的API端点 {endpoint} 在后端不存在"
                })

    # 检查前端组件调用的脚本是否存在
    for component_name, component_info in frontend_components.items():
        for script in component_info["script_calls"]:
            if script not in script_registry.get("functions", {}):
                warnings.append({
                    "type": "missing_script",
                    "component": component_name,
                    "script": script,
                    "message": f"前端组件 {component_name} 调用的脚本 {script} 未在注册表中找到"
                })

    # 检查后端API是否有对应的前端组件使用
    used_endpoints = set()
    for component_info in frontend_components.values():
        used_endpoints.update(component_info["api_endpoints"])

    for endpoint in backend_apis.keys():
        if endpoint not in used_endpoints and not endpoint.startswith("/api/sse"):  # SSE端点特殊处理
            warnings.append({
                "type": "unused_api",
                "endpoint": endpoint,
                "message": f"后端API端点 {endpoint} 没有被前端组件使用"
            })

    return {
        "issues": issues,
        "warnings": warnings,
        "summary": {
            "components": len(frontend_components),
            "apis": len(backend_apis),
            "scripts": len(script_registry.get("functions", {})),
            "issues_count": len(issues),
            "warnings_count": len(warnings)
        }
    }

def generate_report(validation_result: Dict[str, Any]) -> None:
    """生成验证报告"""
    print("=== 前后端映射一致性检查报告 ===")
    print(f"前端组件数: {validation_result['summary']['components']}")
    print(f"后端API数: {validation_result['summary']['apis']}")
    print(f"脚本数: {validation_result['summary']['scripts']}")
    print(f"问题数量: {validation_result['summary']['issues_count']}")
    print(f"警告数量: {validation_result['summary']['warnings_count']}")

    if validation_result['issues']:
        print("\n=== 严重问题 (需要修复) ===")
        for i, issue in enumerate(validation_result['issues'], 1):
            print(f"{i}. [{issue['type']}] {issue['message']}")

    if validation_result['warnings']:
        print("\n=== 警告 (建议检查) ===")
        for i, warning in enumerate(validation_result['warnings'], 1):
            print(f"{i}. [{warning['type']}] {warning['message']}")

    if not validation_result['issues'] and not validation_result['warnings']:
        print("\n✅ 前后端映射完全一致！")

def main():
    """主函数"""
    print("开始前后端映射一致性检查...")

    # 扫描前端组件
    frontend_components = scan_frontend_components()
    print(f"发现 {len(frontend_components)} 个前端组件")

    # 扫描后端API
    backend_apis = scan_backend_apis()
    print(f"发现 {len(backend_apis)} 个后端API端点")

    # 加载脚本注册表
    script_registry = load_script_registry()
    scripts_count = len(script_registry.get("functions", {}))
    print(f"加载 {scripts_count} 个脚本注册信息")

    # 验证映射
    validation_result = validate_mapping(frontend_components, backend_apis, script_registry)

    # 生成报告
    generate_report(validation_result)

    # 返回退出码
    return 1 if validation_result['summary']['issues_count'] > 0 else 0

if __name__ == "__main__":
    sys.exit(main())