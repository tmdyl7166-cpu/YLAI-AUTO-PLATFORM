import re
import json
from urllib.parse import urljoin

try:
    import requests
except Exception:
    raise SystemExit("requests not installed")

BASE = "http://127.0.0.1:8003"
UA = {"User-Agent": "Mozilla/5.0"}
PAGES = [
    "/pages/index.html",
    "/pages/api-doc.html",
    "/pages/run.html",
    "/pages/monitor.html",
    "/pages/visual_pipeline.html",
]


def get(u):
    return requests.get(u, headers=UA, timeout=15)


def head(u):
    try:
        r = requests.head(u, headers=UA, timeout=15, allow_redirects=False)
        if r.status_code == 405:
            r = requests.get(u, headers=UA, timeout=15, stream=True)
        return r
    except Exception:
        class D:
            status_code = 0
            headers = {}

        return D()


def pages_summary():
    ok = 0
    fail = 0
    for p in PAGES:
        r = get(urljoin(BASE, p))
        if r.status_code != 200:
            fail += 1
            continue
        html = r.text
        if p.endswith("index.html"):
            markers = ["Index 子站", "/static/js/pages/index.js"]
        elif p.endswith("api-doc.html"):
            markers = ["API Playground 子站", "/static/js/pages/api-doc.js"]
        elif p.endswith("run.html"):
            markers = ["企业级机械风大屏", 'id="bgCanvas"']
        elif p.endswith("monitor.html"):
            markers = ["后端控制台", 'id="monitor-status"']
        else:
            markers = ["DAG 可视化", "/static/css/visual_pipeline.css"]
        page_ok = all(m in html for m in markers)
        ok += 1 if page_ok else 0
        fail += 0 if page_ok else 1
    return ok, fail


def assets_summary():
    assets = set()
    for p in PAGES:
        r = get(urljoin(BASE, p))
        if r.status_code != 200:
            continue
        items = re.findall(r'<script[^>]+src="([^"]+)"|<link[^>]+href="([^"]+)"', r.text, flags=re.I)
        for s, l in items:
            u = s or l
            if not u or not u.startswith("/") or u.startswith("http"):
                continue
            assets.add(u)
    assets = sorted(a for a in assets if a.startswith("/static/") or a.startswith("/ai-docker/"))
    okn = 0
    failn = 0
    redirs = 0
    notf = 0
    for a in assets:
        r = head(urljoin(BASE, a))
        c = r.status_code
        if c in (301, 302, 303, 307, 308):
            redirs += 1
            continue
        if c == 404:
            notf += 1
            failn += 1
            continue
        if c != 200:
            failn += 1
            continue
        ctype = r.headers.get("Content-Type", "")
        okmime = True
        if a.endswith(".css") and not re.search(r"text/css|text/plain", ctype, re.I):
            okmime = False
        if a.endswith(".js") and not re.search(r"application/javascript|text/javascript", ctype, re.I):
            okmime = False
        if a.endswith((".woff", ".woff2", ".ttf", ".otf")) and not re.search(
            r"font/|application/font-woff2|application/octet-stream", ctype, re.I
        ):
            okmime = False
        if a.endswith((".png", ".jpg", ".jpeg", ".svg", ".gif")) and not re.search(r"image/", ctype, re.I):
            okmime = False
        clen = r.headers.get("Content-Length")
        bytes_ = int(clen) if (clen and clen.isdigit()) else None
        if not bytes_ or bytes_ <= 0:
            try:
                gr = get(urljoin(BASE, a))
                bytes_ = len(gr.content)
            except Exception:
                bytes_ = 0
        if okmime and bytes_ > 0:
            okn += 1
        else:
            failn += 1
    return okn, failn, redirs, notf


def apis_summary():
    ok = True
    try:
        d = get(urljoin(BASE, "/health?fast=1")).json()
        ok &= isinstance(d, dict) and d.get("code") == 0 and isinstance(d.get("data"), dict)
    except Exception:
        ok = False
    try:
        d = get(urljoin(BASE, "/scripts")).json()
        ok &= isinstance(d, dict) and d.get("code") == 0 and isinstance(d.get("data"), list) and bool(d.get("data"))
    except Exception:
        ok = False
    try:
        d = get(urljoin(BASE, "/api/status")).json()
        ok &= isinstance(d, dict) and d.get("code") == 0 and isinstance(d.get("data"), dict) and "markdown" in d["data"]
    except Exception:
        ok = False
    try:
        d = get(urljoin(BASE, "/api/scheduler/config")).json()
        cfg = d.get("data") if isinstance(d, dict) else None
        ok &= (
            isinstance(d, dict)
            and d.get("code") == 0
            and isinstance(cfg, dict)
            and isinstance(cfg.get("max_concurrent_pipelines"), int)
            and cfg.get("max_concurrent_pipelines") >= 1
        )
    except Exception:
        ok = False
    return ok


def main():
    p_ok, p_fail = pages_summary()
    a_ok, a_fail, a_redirs, a_notf = assets_summary()
    api_ok = apis_summary()
    print(f"[SUMMARY] Pages ok: {p_ok}, failed: {p_fail}")
    print(f"[SUMMARY] Assets ok: {a_ok}, failed: {a_fail}, redirects: {a_redirs}, notfound: {a_notf}")
    print("[SUMMARY] APIs: OK" if api_ok else "[SUMMARY] APIs: FAIL")


if __name__ == "__main__":
    main()
