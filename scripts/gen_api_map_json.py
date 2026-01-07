#!/usr/bin/env python3
import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MD_FILE = ROOT / "docs" / "统一接口映射表.md"
OUT_DIR = ROOT / "frontend" / "pages" / "data"
MODULE_STATUS_FILE = OUT_DIR / "module-status.json"
ROUTES_STATUS_FILE = OUT_DIR / "module-routes-status.json"


def parse_markdown(md_text: str):
    modules = {}
    routes = []

    # Patterns
    module_header_re = re.compile(r"\*\*([^\*\n]+)\(node\.(\w+)\)\*\*")
    route_line_re = re.compile(r"-\s*接口:\s*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*`([^`]+)`")
    inline_route_re = re.compile(r"`(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+([^`\s]+)\s*`")

    current_module_id = None
    current_module_title = None

    for line in md_text.splitlines():
        # Detect module section heading like **1.1 参数部署(node.params)**
        m = module_header_re.search(line)
        if m:
            current_module_title = m.group(1).strip()
            current_module_id = m.group(2).strip()
            if current_module_id not in modules:
                modules[current_module_id] = {
                    "id": current_module_id,
                    "title": current_module_title,
                    "status": "🔴",
                }
            continue

        # Extract table-style route lines
        r = route_line_re.search(line)
        if r and current_module_id:
            method, path = r.group(1), r.group(2)
            routes.append({
                "module": current_module_id,
                "chapter": current_module_title,
                "method": method,
                "path": path,
                "status": "🔴",
            })
            continue

        # Extract bullet inline route definitions like: - 提交识别: `POST /api/recognize/submit`
        ir = inline_route_re.search(line)
        if ir and current_module_id:
            method, path = ir.group(1), ir.group(2)
            routes.append({
                "module": current_module_id,
                "chapter": current_module_title,
                "method": method,
                "path": path,
                "status": "🔴",
            })

    return modules, routes


def main():
    if not MD_FILE.exists():
        raise FileNotFoundError(f"Mapping markdown not found: {MD_FILE}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    md_text = MD_FILE.read_text(encoding="utf-8")
    modules, routes = parse_markdown(md_text)

    # Write module-status.json as an object keyed by module id
    module_status_obj = {mid: {"title": m["title"], "status": m["status"]} for mid, m in modules.items()}
    MODULE_STATUS_FILE.write_text(json.dumps(module_status_obj, ensure_ascii=False, indent=2), encoding="utf-8")

    # Write module-routes-status.json as an array of route entries
    ROUTES_STATUS_FILE.write_text(json.dumps(routes, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Generated: {MODULE_STATUS_FILE}")
    print(f"Generated: {ROUTES_STATUS_FILE}")


if __name__ == "__main__":
    main()
