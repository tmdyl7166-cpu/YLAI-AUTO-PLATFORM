#!/usr/bin/env python3
import os
import sys
import time
import json
from typing import Any, Dict, List

import requests

BASE_URL = os.environ.get("BASE_URL", "http://127.0.0.1:8001").rstrip("/")
TIMEOUT = float(os.environ.get("E2E_TIMEOUT", "20"))  # seconds
SLEEP = float(os.environ.get("E2E_POLL_INTERVAL", "0.5"))

# Minimal two-node DAG: A -> B (B depends on A)
NODES = [
    {
        "id": "A",
        "script": "demo",
        "params": {"message": "e2e"
        },
        "depends_on": [],
    },
    {
        "id": "B",
        "script": "monitor",
        "params": {"duration": 1, "interval": 1},
        "depends_on": ["A"],
    },
]


def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"code": 1, "error": f"non-json response: {r.text[:200]}"}


def _get(path: str) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    try:
        return r.json()
    except Exception:
        return {"code": 1, "error": f"non-json response: {r.text[:200]}"}


def main() -> int:
    # Validate
    payload = {"nodes": NODES, "max_concurrency": 2, "priority": 50}
    v = _post("/api/pipeline/validate", payload)
    if v.get("code") != 0:
        print(json.dumps({"stage": "validate", "result": v}, ensure_ascii=False))
        return 2

    # Run
    run = _post("/api/pipeline/run", payload)
    if run.get("code") != 0:
        print(json.dumps({"stage": "run", "result": run}, ensure_ascii=False))
        return 3
    task_id = run.get("task_id")
    if not task_id:
        print(json.dumps({"stage": "run", "error": "missing task_id"}, ensure_ascii=False))
        return 3

    # Poll tasks
    t0 = time.perf_counter()
    last = None
    while time.perf_counter() - t0 < TIMEOUT:
        lst = _get("/api/tasks")
        data = lst.get("data") or []
        for item in data:
            if item.get("task_id") == task_id:
                last = item
                status = item.get("status")
                if status in ("done", "failed"):
                    out = {"stage": "wait", "task": item}
                    print(json.dumps(out, ensure_ascii=False))
                    return 0 if status == "done" else 4
        time.sleep(SLEEP)

    print(json.dumps({"stage": "wait", "error": "timeout", "last": last}, ensure_ascii=False))
    return 5


if __name__ == "__main__":
    sys.exit(main())
