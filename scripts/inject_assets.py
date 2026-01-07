#!/usr/bin/env python3
"""
Inject common head/footer and asset version into frontend pages.
- Replaces __HEAD__/__FOOTER__ placeholders when present.
- Substitutes __ASSET_VERSION__ with env ASSET_VERSION or timestamp.
"""
import os, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = ROOT / "frontend" / "pages"
ASSET_VERSION = os.getenv("ASSET_VERSION", str(int(time.time())))

COMMON_HEAD = """
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
"""
COMMON_FOOTER = """<!-- common footer -->"""

def process_file(fp: Path):
    txt = fp.read_text(encoding="utf-8")
    txt = txt.replace("__HEAD__", COMMON_HEAD)
    txt = txt.replace("__FOOTER__", COMMON_FOOTER)
    txt = txt.replace("__ASSET_VERSION__", ASSET_VERSION)
    fp.write_text(txt, encoding="utf-8")
    return True

def main():
    changed = []
    for fp in PAGES.glob("*.html"):
        try:
            if "__HEAD__" in fp.read_text(encoding="utf-8") or "__ASSET_VERSION__" in fp.read_text(encoding="utf-8"):
                process_file(fp)
                changed.append(fp.name)
        except Exception:
            pass
    print({"ok": True, "changed": changed, "asset_version": ASSET_VERSION})

if __name__ == "__main__":
    main()
