#!/usr/bin/env python3
import json
import re
import sys
import time
import urllib.request as u
import urllib.error as ue
from typing import List, Tuple

BASE = 'http://127.0.0.1:8001'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari'

# Disable proxies to ensure local requests don't go through system proxy
try:
    _opener = u.build_opener(u.ProxyHandler({}))
    u.install_opener(_opener)
except Exception:
    pass

PAGES = [
    '/pages/index.html',
    '/pages/api-doc.html',
    '/pages/run.html',
    '/pages/monitor.html',
    '/pages/visual_pipeline.html',
]

MARKERS = {
    '/pages/index.html': [
        'Index 子站',
        '/static/js/pages/index.js',
    ],
    '/pages/api-doc.html': [
        'API Playground 子站',
        '/static/js/pages/api-doc.js',
    ],
    '/pages/run.html': [
        '企业级机械风大屏',
        'id="bgCanvas"',
    ],
    '/pages/monitor.html': [
        '后端控制台',
        'id="monitor-status"',
    ],
    '/pages/visual_pipeline.html': [
        'DAG 可视化',
        '/static/css/visual_pipeline.css',
    ],
}


def fetch(path: str, method: str = 'GET', data: bytes = None, timeout: float = 8.0):
    req = u.Request(BASE + path, data=data, method=method, headers={'User-Agent': UA})
    try:
        with u.urlopen(req, timeout=timeout) as r:
            body = r.read()
            return r.status, r.headers, body
    except ue.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b''
        return getattr(e, 'code', 0) or 0, getattr(e, 'headers', {}), body
    except Exception:
        return 0, {}, b''


def wait_health(max_wait: int = 20) -> bool:
    for _ in range(max_wait):
        st, _, _ = fetch('/health')
        if st == 200:
            return True
        time.sleep(1)
    return False


def page_checks() -> dict:
    results = {"ok": True, "items": []}
    for p in PAGES:
        st, _, body = fetch(p)
        item = {"path": p, "status": st, "markers": []}
        if st != 200:
            item["ok"] = False
            results["ok"] = False
            results["items"].append(item)
            continue
        text = body.decode('utf-8', errors='ignore')
        ok = True
        for m in MARKERS.get(p, []):
            has = (m in text)
            item["markers"].append({"marker": m, "has": has})
            ok = ok and has
        item["ok"] = ok
        if not ok:
            results["ok"] = False
        results["items"].append(item)
    return results


SRC_HREF_RE = re.compile(r'(?:src|href)="([^"]+)"', re.I)


def collect_assets() -> List[str]:
    urls = set()
    for p in PAGES:
        st, _, body = fetch(p)
        if st != 200:
            continue
        text = body.decode('utf-8', errors='ignore')
        for m in SRC_HREF_RE.finditer(text):
            url = m.group(1)
            if url.startswith('http://') or url.startswith('https://'):
                continue
            if url.startswith('/'):
                urls.add(url)
    return sorted(urls)


def _hdr_get_case_insensitive(h: dict, key: str, default: str = '') -> str:
    for k, v in h.items():
        if k.lower() == key.lower():
            return v
    return default


def head_or_get(url: str) -> Tuple[int, dict]:
    # Try HEAD first, fallback to GET
    st, hdrs, _ = fetch(url, method='HEAD')
    dh = dict(hdrs)
    # Fallback when HEAD lacks critical headers even if 200
    if st == 0 or st >= 400 or not _hdr_get_case_insensitive(dh, 'Content-Type'):
        st, hdrs, _ = fetch(url, method='GET')
        dh = dict(hdrs)
    return st, dh


def asset_checks() -> dict:
    assets = [a for a in collect_assets() if a.startswith('/static/') or a.startswith('/ai-docker/')]
    res = {"ok": True, "total": len(assets), "failed": 0, "items": []}
    for a in assets:
        st, hdr = head_or_get(a)
        ctype = _hdr_get_case_insensitive(hdr, 'Content-Type')
        ok = (st == 200)
        if ok:
            # 严格模式：必须有 Content-Type 且与扩展匹配
            if a.endswith('.css'):
                ok = bool(re.search(r'text/css', ctype, re.I))
            elif a.endswith('.js'):
                ok = bool(re.search(r'application/javascript|text/javascript', ctype, re.I))
            elif re.search(r'\.(woff2?|ttf|otf)$', a, re.I):
                ok = bool(re.search(r'font/|application/', ctype, re.I))
            elif re.search(r'\.(png|jpe?g|svg|gif)$', a, re.I):
                ok = bool(re.search(r'image/', ctype, re.I))
        if not ok:
            res["ok"] = False
            res["failed"] += 1
        res["items"].append({"url": a, "status": st, "content_type": ctype, "ok": ok})
    return res


def api_checks() -> dict:
    ok = True
    summary = []
    st, _, b = fetch('/health')
    try:
        d = json.loads(b)
        cond = (st == 200 and isinstance(d, dict) and d.get('code') == 0 and isinstance(d.get('data'), dict))
    except Exception:
        cond = False
    ok &= cond
    summary.append({"path": "/health", "ok": cond, "status": st})

    st, _, b = fetch('/scripts')
    try:
        d = json.loads(b)
        cond = (st == 200 and isinstance(d, dict) and d.get('code') == 0 and isinstance(d.get('data'), list))
    except Exception:
        cond = False
    ok &= cond
    summary.append({"path": "/scripts", "ok": cond, "status": st})

    st, _, b = fetch('/api/status')
    try:
        d = json.loads(b)
        cond = ((st == 200 and isinstance(d, dict) and d.get('code') == 0 and isinstance(d.get('data'), dict) and 'markdown' in d['data']) or st == 401)
    except Exception:
        cond = False
    ok &= cond
    summary.append({"path": "/api/status", "ok": cond, "status": st})

    # modules endpoint may require auth; treat 401 as acceptable
    st, _, _ = fetch('/api/modules')
    summary.append({"path": "/api/modules", "status": st, "ok": (st == 200 or st == 401)})

    # info endpoint (existence only)
    st, _, _ = fetch('/api/pipeline/run')
    summary.append({"path": "/api/pipeline/run", "status": st})
    return {"ok": ok, "items": summary}


def main():
    if not wait_health(20):
        print(json.dumps({"ok": False, "error": "backend not healthy"}, ensure_ascii=False))
        return 1
    pages = page_checks()
    assets = asset_checks()
    apis = api_checks()
    ok = pages["ok"] and assets["ok"] and apis["ok"]
    report = {
        "ok": ok,
        "pages_ok": pages["ok"],
        "assets_ok": assets["ok"],
        "apis_ok": apis["ok"],
        "assets_total": assets["total"],
        "assets_failed": assets["failed"],
    }
    if not assets["ok"]:
        # include failing asset details to aid diagnosis
        report["asset_items"] = [i for i in assets["items"] if not i.get("ok")]
    if not pages["ok"]:
        report["page_items"] = pages["items"]
    print(json.dumps(report, ensure_ascii=False))
    return 0 if ok else 2


if __name__ == '__main__':
    sys.exit(main())
