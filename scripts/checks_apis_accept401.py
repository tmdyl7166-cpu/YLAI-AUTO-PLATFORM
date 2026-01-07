#!/usr/bin/env python3
import json
import sys
import os
import time
from typing import Tuple

try:
    import requests  # 优先使用 requests，便于超时控制与文本截取
except Exception:
    requests = None

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:8001")
TIMEOUT = float(os.environ.get("CHECK_TIMEOUT", "3.0"))

PATHS = [
    ("/health", (200,)),
    ("/scripts", (200,)),
    ("/api/status", (200, 401)),
    ("/api/modules", (200, 401)),
]


def check_requests(url: str, expects: Tuple[int, ...]) -> Tuple[bool, int, str]:
    try:
        assert requests is not None
        resp = requests.get(url, timeout=TIMEOUT)
        code = resp.status_code
        ok = code in expects
        sample = resp.text[:256] if hasattr(resp, "text") else ""
        return ok, code, sample
    except Exception as e:
        return False, -1, str(e)


def check_urllib(url: str, expects: Tuple[int, ...]) -> Tuple[bool, int, str]:
    import urllib.request
    import urllib.error
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            code = resp.status
            ok = code in expects
            return ok, code, ""
    except urllib.error.HTTPError as e:
        code = e.code
        ok = code in expects
        return ok, code, str(e)
    except Exception as e:
        return False, -1, str(e)


def main():
    results = []
    all_ok = True
    for path, expects in PATHS:
        url = BASE + path
        if requests is not None:
            ok, code, sample = check_requests(url, expects)
        else:
            ok, code, sample = check_urllib(url, expects)
        results.append({
            "path": path,
            "url": url,
            "status": code,
            "expects": list(expects),
            "ok": ok,
            "sample": sample,
        })
        if not ok:
            all_ok = False

    payload = {
        "summary": {
            "base": BASE,
            "all_ok": all_ok,
            "timestamp": int(time.time()),
        },
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    sys.exit(0 if all_ok else 3)


if __name__ == "__main__":
    main()
