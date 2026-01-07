import asyncio
import os
from typing import List

from backend.core.logger import logger


async def _probe_once(
    app,
    base: str,
    interval: float,
    iterations: int,
    api_paths: List[str],
    check_assets: bool,
    pages: List[str] | None = None,
):
    try:
        # 组合参数；仅当提供 pages 时传入，避免覆盖脚本默认值
        kwargs = dict(
            base=base,
            interval=interval,
            iterations=iterations,
            api_paths=api_paths,
            check_assets=check_assets,
        )
        if pages:
            kwargs["pages"] = pages

        # kernel.run 是同步方法，放入线程避免阻塞事件循环
        await asyncio.to_thread(
            app.state.kernel.run,
            "page_probe",
            **kwargs,
        )
    except Exception as e:
        logger.error(f"auto_probe run failed: {e}")


async def start_auto_probe(app):
    enabled = os.getenv("AUTO_PROBE", "1").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    if not enabled:
        logger.info("auto_probe disabled (set AUTO_PROBE=1 to enable)")
        return

    base = os.getenv("AUTO_PROBE_BASE", "http://127.0.0.1:8001")
    interval = float(os.getenv("AUTO_PROBE_INTERVAL", "1.0"))      # 单页内部请求间隔
    iterations = int(os.getenv("AUTO_PROBE_ITERATIONS", "6"))      # 每轮页内请求次数
    gap = float(os.getenv("AUTO_PROBE_GAP", "8.0"))                # 轮与轮之间的间隔
    apis_str = os.getenv("AUTO_PROBE_APIS", "/health,/api/modules")
    api_paths = [p for p in apis_str.split(",") if p]
    check_assets = os.getenv("AUTO_PROBE_ASSETS", "1").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    pages_env = os.getenv("AUTO_PROBE_PAGES")
    pages = (
        [p.strip() for p in pages_env.split(",") if p.strip()]
        if pages_env
        else None
    )

    logger.info(
        "auto_probe enabled base=%s interval=%ss iterations=%s gap=%ss",
        base,
        interval,
        iterations,
        gap,
    )
    logger.info(
        "auto_probe params apis=%s assets=%s pages=%s",
        api_paths,
        check_assets,
        pages if pages else "default",
    )

    async def loop():
        while True:
            await _probe_once(
                app,
                base,
                interval,
                iterations,
                api_paths,
                check_assets,
                pages,
            )
            await asyncio.sleep(gap)

    # 后台启动，不阻塞启动流程
    asyncio.create_task(loop())
