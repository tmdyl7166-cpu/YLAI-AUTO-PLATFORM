import re


def detect_unfinished_content(text: str):
    unfinished = []
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"(TODO|FIXME|pass|NotImplemented)", line):
            unfinished.append({"line": i, "content": line})
    return unfinished


def analyze_dependencies(file_path):
    imports = []
    calls = []
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            s = line.strip()
            if s.startswith("import") or s.startswith("from"):
                imports.append(s)
            if "(" in s and ")" in s:
                calls.append(s)
    return {"imports": imports, "calls": calls}
