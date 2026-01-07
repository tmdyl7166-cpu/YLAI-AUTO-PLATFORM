from __future__ import annotations

import json
import time
from typing import Dict, List, Optional
import re
from urllib.parse import urljoin

import requests

from backend.core.base import BaseScript
from backend.core.registry import registry
from backend.core.logger import logger, ws_logger, emit_ws
import threading

_lock = threading.Lock()
_running = False


@registry.register("page_probe")
class PageProbeScript(BaseScript):
    name = "page_probe"

    async def run(self, **kwargs) -> Dict:
        """
        页面探测任务
        参数:
            base (str): 基础URL，默认 'http://127.0.0.1:8001'
            pages (List[str]): 需探测的页面路径列表
        返回:
            dict: 探测结果或错误信息
        异常:
            捕获并返回脚本运行冲突或其他异常
        """
        global _running
        if not _lock.acquire(blocking=False):
            return {"status": "busy", "error": "page_probe already running"}
        if _running:
            _lock.release()
            return {"status": "busy", "error": "page_probe already running"}
        _running = True
        base: str = kwargs.get("base", "http://127.0.0.1:8001")
        pages: List[str] = kwargs.get(
            "pages",
            [
                "/pages/index.html",
                "/pages/api-doc.html",
                "/pages/run.html",
                "/pages/monitor.html",
                "/pages/visual_pipeline.html",
            ],
        )
        # 额外探测项
        api_paths: List[str] = kwargs.get("api_paths", ["/health", "/api/modules"])
        check_assets: bool = bool(kwargs.get("check_assets", True))
        page_markers: Dict[str, List[str]] = kwargs.get("page_markers", {
            "/pages/index.html": ["<title>Index 子站</title>", "/static/js/pages/index.js", "夜灵多功能检测仪"],
            "/pages/api-doc.html": ["<title>API Playground 子站</title>", "/static/css/api-doc.css", "/static/js/pages/api-doc.js", "API Playground"],
            "/pages/run.html": ["<title>YLAI 企业级机械风大屏</title>", "/static/css/run.css", "id=\"bgCanvas\""],
            "/pages/monitor.html": ["<title>后端控制台</title>", "/static/js/pages/monitor.js", "id=\"monitor-status\""],
            "/pages/visual_pipeline.html": ["<title>企业级 DAG 可视化流水线</title>", "/static/css/visual_pipeline.css", "id=\"tasksList\""]
        })
        interval: float = float(kwargs.get("interval", 3.0))
        iterations: int | None = kwargs.get("iterations")
        duration: float | None = kwargs.get("duration")  # 秒

        # 计算循环次数优先级：iterations > duration > 1
        if iterations is None:
            if duration:
                iterations = max(1, int(duration // interval) + 1)
            else:
                iterations = 1

        session = requests.Session()
        ua = kwargs.get("ua") or (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome Safari"
        )
        headers = {"User-Agent": ua}

        logger.info(f"🫧 页面探测启动 base={base} interval={interval}s iterations={iterations}")

        results: List[Dict] = []
        assets_checked = 0
        assets_ok = 0
        api_checked = 0
        api_ok = 0
        markers_checked = 0
        markers_ok = 0
        start = time.perf_counter()
        try:
            for i in range(int(iterations)):
                cycle: List[Dict] = []
                for path in pages:
                    url = f"{base}{path}"
                    t0 = time.perf_counter()
                    ok = False
                    code = None
                    ctype = None
                    size = None
                    err = None
                    html: Optional[str] = None
                    try:
                        resp = session.get(url, headers=headers, timeout=8)
                        code = resp.status_code
                        ctype = resp.headers.get("Content-Type", "")
                        size = len(resp.content)
                        ok = (code == 200 and "text/html" in ctype.lower())
                        html = resp.text if ok else None
                    except Exception as e:
                        err = str(e)
                        ok = False
                    t1 = time.perf_counter()
                    item = {
                        "url": url,
                        "path": path,
                        "ms": int((t1 - t0) * 1000),
                        "code": code,
                        "ok": ok,
                        "ctype": ctype,
                        "size": size,
                        "error": err,
                        "ts": int(time.time()),
                        "seq": i + 1,
                    }
                    cycle.append(item)
                    # 结构化推送到 WS 订阅者（monitor.html 可直接展示）
                    try:
                        payload = json.dumps({"type": "PAGE_HEALTH", "data": item}, ensure_ascii=False)
                        ws_logger.info("PAGE_HEALTH %s", payload)
                        # 在线程上下文中仅当存在运行中的事件循环时再派发
                        import asyncio
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(emit_ws(payload))
                        except RuntimeError:
                            # 无运行中的事件循环（如在 to_thread 线程中），跳过 WS 推送
                            pass
                    except Exception:
                        pass

                    # 页面标记断言（可选）
                    markers = page_markers.get(path) or []
                    if markers and html:
                        for m in markers:
                            ok_m = (m in html)
                            markers_checked += 1
                            if ok_m:
                                markers_ok += 1
                            try:
                                payload = json.dumps({"type": "MARKER_ASSERT", "data": {"path": path, "marker": m, "ok": ok_m, "seq": i + 1}}, ensure_ascii=False)
                                ws_logger.info("MARKER_ASSERT %s", payload)
                                import asyncio
                                try:
                                    loop = asyncio.get_running_loop()
                                    loop.create_task(emit_ws(payload))
                                except RuntimeError:
                                    pass
                            except Exception:
                                pass

                    # 从页面抽取静态资源并校验 MIME（可选）
                    if check_assets and html:
                        try:
                            tags = re.findall(r'<script[^>]+src="([^"]+)"|<link[^>]+href="([^"]+)"', html, flags=re.I)
                            urls: List[str] = []
                            for a, b in tags:
                                u = a or b
                                if not u:
                                    continue
                                if u.startswith("http://") or u.startswith("https://"):
                                    continue
                                abs_u = urljoin(base + "/", u)
                                urls.append(abs_u)
                            # 去重
                            seen = set()
                            deduped: List[str] = []
                            for _u in urls:
                                if _u not in seen:
                                    seen.add(_u)
                                    deduped.append(_u)
                            urls = deduped
                            for au in urls:
                                at0 = time.perf_counter()
                                acode = None
                                actype = None
                                aok = False
                                try:
                                    # HEAD 有站点不支持，降级 GET stream
                                    r = session.head(au, timeout=6)
                                    acode = r.status_code
                                    actype = r.headers.get("Content-Type", "")
                                    if acode != 200 or not actype:
                                        r = session.get(au, timeout=8)
                                        acode = r.status_code
                                        actype = r.headers.get("Content-Type", "")
                                    aok = (acode == 200 and bool(actype))
                                except Exception:
                                    aok = False
                                finally:
                                    assets_checked += 1
                                    if aok:
                                        assets_ok += 1
                                at1 = time.perf_counter()
                                try:
                                    payload = json.dumps({"type": "ASSET_CHECK", "data": {"url": au, "code": acode, "ctype": actype, "ok": aok, "ms": int((at1-at0)*1000)}}, ensure_ascii=False)
                                    ws_logger.info("ASSET_CHECK %s", payload)
                                    import asyncio
                                    try:
                                        loop = asyncio.get_running_loop()
                                        loop.create_task(emit_ws(payload))
                                    except RuntimeError:
                                        pass
                                except Exception:
                                    pass

                        except Exception:
                            # 资源提取与校验过程的兜底保护，避免一次异常中断整个探测循环
                            pass

                # 周期汇总日志
                good = sum(1 for r in cycle if r.get("ok"))
                logger.info(f"🫧 周期#{i+1}: {good}/{len(cycle)} OK")
                results.extend(cycle)
                if i < iterations - 1:
                    time.sleep(interval)

                # API 端点健康（每周期探测一次）
                for ap in api_paths:
                    api_url = urljoin(base + "/", ap)
                    a0 = time.perf_counter()
                    acode = None
                    aok = False
                    err = None
                    try:
                        rr = session.get(api_url, headers=headers, timeout=6)
                        acode = rr.status_code
                        aok = (acode == 200)
                        try:
                            j = rr.json()
                            if isinstance(j, dict) and j.get("code") == 0:
                                aok = True
                        except Exception:
                            pass
                    except Exception as e:
                        err = str(e)
                        aok = False
                    a1 = time.perf_counter()
                    api_checked += 1
                    if aok:
                        api_ok += 1
                    try:
                        payload = json.dumps({"type": "API_HEALTH", "data": {"url": api_url, "code": acode, "ok": aok, "ms": int((a1-a0)*1000), "error": err}}, ensure_ascii=False)
                        ws_logger.info("API_HEALTH %s", payload)
                        import asyncio
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(emit_ws(payload))
                        except RuntimeError:
                            pass
                    except Exception:
                        pass

            total_ms = int((time.perf_counter() - start) * 1000)
            summary = {
                "cycles": int(iterations),
                "count": len(results),
                "ok": sum(1 for r in results if r.get("ok")),
                "ms": total_ms,
                "assets": {"ok": assets_ok, "total": assets_checked},
                "apis": {"ok": api_ok, "total": api_checked},
                "markers": {"ok": markers_ok, "total": markers_checked},
            }
            logger.info(
                f"✅ 页面探测完成 cycles={summary['cycles']} ok={summary['ok']}/{summary['count']} t={summary['ms']}ms"
            )
            return {"status": "success", "summary": summary, "results": results}
        except KeyboardInterrupt:
            logger.warning("⚠️ 页面探测被中断")
            return {"status": "cancelled"}
        except Exception as e:
            logger.error(f"❌ 页面探测失败: {e}")
            return {"status": "error", "error": str(e)}
        finally:
            _running = False
            try:
                _lock.release()
            except Exception:
                pass
