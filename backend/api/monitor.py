from fastapi import APIRouter, WebSocket
import asyncio
import os
from pathlib import Path
from backend.services.monitoring_service import monitoring_service

router = APIRouter()

# 连接集合与文件监听任务句柄
_clients: set[WebSocket] = set()
_watch_task: asyncio.Task | None = None


async def _broadcast_reload():
    if not _clients:
        return
    dead = []
    for ws in list(_clients):
        try:
            await ws.send_json({"type": "reload"})
        except Exception:
            dead.append(ws)
    for ws in dead:
        try:
            _clients.discard(ws)
            await ws.close()
        except Exception:
            pass


_debounce_task: asyncio.Task | None = None
_pending_event: bool = False


def _get_debounce_ms() -> int:
    try:
        v = int(os.getenv("HX_DEBOUNCE_MS", "300"))
        return max(100, min(v, 1000))  # 安全范围：100ms~1000ms
    except Exception:
        return 300


async def _debounced_broadcast(delay_ms: int | None = None):
    global _debounce_task, _pending_event
    _pending_event = True
    # 若已有定时器，直接返回，等待其触发
    if _debounce_task and not _debounce_task.done():
        return
    async def _timer():
        global _debounce_task, _pending_event
        try:
            # 将多个短时间事件合并
            ms = delay_ms if delay_ms is not None else _get_debounce_ms()
            await asyncio.sleep(ms / 1000.0)
            if _pending_event:
                _pending_event = False
                # 非阻塞式广播，避免长连接影响定时器
                asyncio.create_task(_broadcast_reload())
        finally:
            _debounce_task = None
    loop = asyncio.get_running_loop()
    _debounce_task = loop.create_task(_timer())


async def _file_watcher_loop(frontend_dir: Path):
    # 首选 watchfiles，回退到轮询
    try:
        from watchfiles import awatch  # type: ignore
        async for _changes in awatch(str(frontend_dir)):
            # 去抖：文件变更事件触发合并
            await _debounced_broadcast()
    except Exception:
        # 轮询模式：记录最近的目录修改时间，定期检查
        EXT_ALLOW = {".js", ".css", ".html"}

        def _latest_mtime(p: Path) -> float:
            last = 0.0
            for root, _dirs, files in os.walk(p):
                for f in files:
                    try:
                        # 仅关注前端相关扩展，降低IO
                        if os.path.splitext(f)[1].lower() not in EXT_ALLOW:
                            continue
                        m = os.path.getmtime(os.path.join(root, f))
                        if m > last:
                            last = m
                    except Exception:
                        pass
            return last

        last_mtime = _latest_mtime(frontend_dir)
        while True:
            await asyncio.sleep(1.0)
            cur = _latest_mtime(frontend_dir)
            if cur > last_mtime:
                last_mtime = cur
                await _debounced_broadcast()


def _ensure_watcher_started():
    global _watch_task
    if _watch_task and not _watch_task.done():
        return
    # 前端目录：与 app.py 中静态挂载一致
    root = Path(__file__).resolve().parents[2]  # 到仓库根
    frontend_dir = (root / "frontend").resolve()
    if not frontend_dir.exists():
        return
    loop = asyncio.get_running_loop()
    _watch_task = loop.create_task(_file_watcher_loop(frontend_dir))


@router.websocket("/ws/monitor")
async def ws_monitor(websocket: WebSocket):
    await websocket.accept()
    _clients.add(websocket)
    # 记录WebSocket连接监控指标
    monitoring_service.record_websocket_connection("monitor", "connected")
    # 确保文件监听任务已启动
    _ensure_watcher_started()
    try:
        while True:
            # 前端无需发送内容；保持连接即可
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        _clients.discard(websocket)
        # 记录WebSocket断开监控指标
        monitoring_service.record_websocket_connection("monitor", "disconnected")
        try:
            await websocket.close()
        except Exception:
            pass
