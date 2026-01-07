#!/usr/bin/env python3
"""
Validate frontend pages for unified structure:
- No leftover placeholders: __HEAD__, __FOOTER__, __ASSET_VERSION__
- Contains common head marker: <meta charset="UTF-8">
- Basic HTML well-formed checks (doctype/head/body presence heuristics)

Exit non-zero if any page fails.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
PAGES = (ROOT / "frontend" / "pages").resolve()

REQUIRED_SNIPPETS = [
    '<meta charset="UTF-8">',
]

FORBIDDEN_MARKERS = [
    "__HEAD__",
    "__FOOTER__",
    "__ASSET_VERSION__",
]

def validate_file(fp: Path):
    txt = fp.read_text(encoding="utf-8", errors="ignore")
    issues = []
    # Forbidden placeholders
    for m in FORBIDDEN_MARKERS:
        if m in txt:
            issues.append(f"leftover placeholder: {m}")
    # Required snippets
    for s in REQUIRED_SNIPPETS:
        if s not in txt:
            issues.append(f"missing snippet: {s}")
    # Heuristic HTML structure
    low = txt.lower()
    if ("<html" not in low) or ("<head" not in low) or ("<body" not in low):
        issues.append("missing basic html structure (html/head/body)")
    return issues

def main():
    if not PAGES.exists():
        print({"ok": False, "error": f"pages dir not found: {PAGES}"})
        sys.exit(2)
    failed = {}
    for fp in sorted(PAGES.glob("*.html")):
        issues = validate_file(fp)
        if issues:
            failed[fp.name] = issues
    if failed:
        print({"ok": False, "failed": failed})
        sys.exit(3)
    print({"ok": True, "checked": len(list(PAGES.glob('*.html')))})
    sys.exit(0)

if __name__ == "__main__":
    main()
