#!/usr/bin/env python3
"""Sync Python requirements from pyproject.toml into backend/requirements.txt

Usage:
  python tools/sync_requirements.py

This script reads `pyproject.toml` in the repo root and writes a
consolidated `backend/requirements.txt` including main dependencies and
dev dependencies useful for CI. It is intentionally simple and safe.
"""
import sys
from pathlib import Path

try:
    import tomllib
except Exception:  # pragma: no cover - older runtimes
    import tomli as tomllib


ROOT = Path(__file__).resolve().parents[1]
PYPROJECT = ROOT / "pyproject.toml"
OUT = ROOT / "backend" / "requirements.txt"


def load_pyproject(path: Path) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def format_requirement(name: str) -> str:
    # name is already a requirement spec (e.g. pkg>=1.2)
    return name


def main() -> int:
    if not PYPROJECT.exists():
        print("pyproject.toml not found", file=sys.stderr)
        return 2
    data = load_pyproject(PYPROJECT)
    deps = []
    proj = data.get("project", {})
    for d in proj.get("dependencies", []) or []:
        deps.append(format_requirement(d))

    opt = proj.get("optional-dependencies", {})
    # include dev extras useful for CI/tests
    for d in opt.get("dev", []) or []:
        deps.append(format_requirement(d))

    # dedupe while preserving order
    seen = set()
    out = []
    for r in deps:
        if r not in seen:
            seen.add(r)
            out.append(r)

    header = (
        "# This file is generated from pyproject.toml by tools/sync_requirements.py\n"
        "# Run: python tools/sync_requirements.py to refresh\n"
        "# Keep pyproject.toml as the source of truth.\n\n"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8") as f:
        f.write(header)
        for line in out:
            f.write(line.rstrip() + "\n")

    print(f"Wrote {len(out)} requirements to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
