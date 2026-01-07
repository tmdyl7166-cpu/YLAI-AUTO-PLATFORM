#!/usr/bin/env python3
"""
Strip per-page JS module includes from HTML pages under frontend/pages,
excluding min-template.html. Only removes <script> tags that reference
static/js/pages/*.js to detach page-specific controllers.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = ROOT / "frontend" / "pages"

SCRIPT_PAT = re.compile(
    r"<script[^>]+src=\"[^\"]*static/js/pages/[^\"]+\"[^>]*></script>",
    re.IGNORECASE,
)

def process_html(fp: Path) -> bool:
    txt = fp.read_text(encoding="utf-8")
    new = SCRIPT_PAT.sub("", txt)
    if new != txt:
        fp.write_text(new, encoding="utf-8")
        return True
    return False

def main():
    changed = []
    for fp in PAGES_DIR.glob("*.html"):
        if fp.name == "min-template.html":
            continue
        try:
            if process_html(fp):
                changed.append(fp.name)
        except Exception:
            pass
    print({"ok": True, "changed": changed})

if __name__ == "__main__":
    main()
