#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path


def strip_json_comments(s: str) -> str:
    # remove // line comments and /* */ block comments in a simple manner
    s = re.sub(r"/\*.*?\*/", "", s, flags=re.S)
    s = re.sub(r"(^|\s)//.*$", "", s, flags=re.M)
    return s


def main():
    root = Path(__file__).resolve().parents[1]
    tasks_file = root / ".vscode" / "tasks.json"
    if not tasks_file.exists():
        print("{}")
        return 0

    raw = tasks_file.read_text(encoding="utf-8")
    data = None
    try:
        data = json.loads(strip_json_comments(raw))
    except Exception as e:
        print(json.dumps({
            "ok": False,
            "error": f"tasks.json JSON parse failed: {e}"
        }, ensure_ascii=False))
        return 1

    tasks = data.get("tasks")
    if not isinstance(tasks, list):
        print(json.dumps({
            "ok": False,
            "error": "tasks is not a list"
        }, ensure_ascii=False))
        return 1

    issues = []
    labels = set()
    for i, t in enumerate(tasks):
        if not isinstance(t, dict):
            issues.append({"index": i, "error": "task is not an object"})
            continue
        label = t.get("label")
        if not label or not isinstance(label, str):
            issues.append({"index": i, "error": "missing or invalid label"})
        else:
            if label in labels:
                issues.append({"index": i, "label": label, "error": "duplicate label"})
            labels.add(label)
        ttype = t.get("type")
        if not ttype or not isinstance(ttype, str):
            issues.append({"index": i, "label": label, "error": "missing or invalid type"})
        if ttype == "shell":
            cmd = t.get("command")
            if not cmd or not isinstance(cmd, str):
                issues.append({"index": i, "label": label, "error": "shell task missing command"})

    ok = len(issues) == 0
    print(json.dumps({
        "ok": ok,
        "task_count": len(tasks),
        "issues": issues
    }, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == "__main__":
    sys.exit(main())
