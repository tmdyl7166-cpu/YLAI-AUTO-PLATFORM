#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "logs" / "container_deps_matrix.json"
OUTPUT = ROOT / "docs" / "CONTAINER_DEPS.md"

def to_table(title, rows):
    out = [f"\n### {title}", "- 项目依赖概览"]
    if not rows:
        out.append("(无)")
        return "\n".join(out)
    out.append("\n| 项目 | 类型 | 项 | 值 |")
    out.append("|---|---|---|---|")
    for r in rows:
        out.append(f"| {r['project']} | {r['kind']} | {r['item']} | {r['value']} |")
    return "\n".join(out)

def main():
    if not INPUT.exists():
        print(f"[error] not found: {INPUT}")
        return 1
    data = json.loads(INPUT.read_text(encoding="utf-8"))
    dockerfiles = data.get("dockerfiles", {})
    compose = data.get("compose", {})
    files = data.get("files", {})

    rows = []
    # Dockerfiles
    for path, installs in dockerfiles.items():
        project = Path(path).name
        for kind in ("apt", "apk", "pip", "npm", "other"):
            vals = installs.get(kind, []) or []
            for v in vals:
                if isinstance(v, dict):
                    rows.append({"project": project, "kind": f"dockerfile:{kind}", "item": list(v.keys())[0], "value": list(v.values())[0]})
                else:
                    rows.append({"project": project, "kind": f"dockerfile:{kind}", "item": "cmd", "value": v})
    # Compose builds
    for path, services in compose.items():
        for svc, meta in services.items():
            if not meta:
                continue
            rows.append({"project": Path(path).name, "kind": "compose:service", "item": svc, "value": json.dumps(meta, ensure_ascii=False)})
    # Files: requirements and package.json deps
    for key, info in files.items():
        project = info.get("path") or key
        if key == "frontend_package":
            deps = info.get("dependencies", {})
            devdeps = info.get("devDependencies", {})
            for k, v in deps.items():
                rows.append({"project": project, "kind": "pkg:dependencies", "item": k, "value": v})
            for k, v in devdeps.items():
                rows.append({"project": project, "kind": "pkg:devDependencies", "item": k, "value": v})
        else:
            for pkg in info.get("packages", []):
                rows.append({"project": project, "kind": "req", "item": pkg.split("==")[0], "value": pkg})

    # Append to docs
    md = OUTPUT.read_text(encoding="utf-8") if OUTPUT.exists() else ""
    md += "\n\n## 依赖摘要表（自动生成）\n"
    md += to_table("容器与依赖概览", rows)
    # Conflicts section
    conflicts = data.get("conflicts", {})
    md += "\n\n### 版本冲突检测\n"
    if conflicts:
        md += "\n| 依赖名 | 版本集合 |\n|---|---|\n"
        for name, vers in sorted(conflicts.items()):
            md += f"| {name} | {', '.join(vers)} |\n"
    else:
        md += "(无冲突)\n"
    OUTPUT.write_text(md, encoding="utf-8")
    print(f"[ok] written: {OUTPUT}")

if __name__ == "__main__":
    raise SystemExit(main())
