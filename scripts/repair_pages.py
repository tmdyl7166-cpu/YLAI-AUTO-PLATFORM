#!/usr/bin/env python3
"""
Auto-repair common issues in frontend pages. By default dry-run and print suggestions.
Usage:
  python scripts/repair_pages.py         # dry-run, print suggestions
  APPLY=1 python scripts/repair_pages.py # apply fixes in-place
"""
from pathlib import Path
import os
import json

ROOT = Path(__file__).resolve().parents[1]
PAGES = (ROOT / "frontend" / "pages").resolve()

COMMON_HEAD = (
    '    <meta charset="UTF-8">\n'
    '    <meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
)

APPLY = os.getenv("APPLY", "0") not in ("0", "false", "False")

def suggest_and_fix(fp: Path):
    txt = fp.read_text(encoding="utf-8", errors="ignore")
    orig = txt
    issues = []
    fixes = []
    # Remove placeholders
    for m in ("__HEAD__", "__FOOTER__", "__ASSET_VERSION__"):
        if m in txt:
            issues.append(f"leftover placeholder: {m}")
            txt = txt.replace(m, "")
            fixes.append(f"replace {m} -> ''")
    # Ensure meta charset
    if '<meta charset="UTF-8">' not in txt:
        issues.append("missing <meta charset>")
        # naive inject after <head>
        low = txt.lower()
        idx = low.find("<head>")
        if idx != -1:
            idx2 = idx + len("<head>")
            txt = txt[:idx2] + "\n" + COMMON_HEAD + txt[idx2:]
            fixes.append("insert COMMON_HEAD after <head>")
    changed = (txt != orig)
    if APPLY and changed:
        fp.write_text(txt, encoding="utf-8")
    return {"issues": issues, "fixes": fixes, "changed": changed}

def main():
    if not PAGES.exists():
        print(json.dumps({"ok": False, "error": f"pages dir not found: {PAGES}"}, ensure_ascii=False))
        return 2
    report = {}
    for fp in sorted(PAGES.glob("*.html")):
        res = suggest_and_fix(fp)
        if res["issues"] or res["changed"]:
            report[fp.name] = res
    ok = all(not v["issues"] for v in report.values())
    print(json.dumps({"ok": ok, "apply": APPLY, "report": report}, ensure_ascii=False, indent=2))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
