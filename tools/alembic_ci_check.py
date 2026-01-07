#!/usr/bin/env python3
"""CI helper to validate Alembic migrations by generating SQL for upgrade head.

Usage:
  DATABASE_URL=postgresql://user:pass@host/db python tools/alembic_ci_check.py

This will configure Alembic to use the provided DATABASE_URL and request a
SQL-only upgrade to head. It verifies that migrations can be rendered without
applying them.
"""
import os
import sys
from alembic.config import Config
from alembic import command


def main():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL is not set", file=sys.stderr)
        return 2

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)

    try:
        # sql=True renders SQL to stdout instead of applying
        command.upgrade(cfg, "head", sql=True)
    except Exception as e:
        print("Alembic check failed:", e, file=sys.stderr)
        return 3

    print("Alembic check succeeded (SQL rendered)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
