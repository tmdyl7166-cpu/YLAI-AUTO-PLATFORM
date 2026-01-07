import asyncio
import itertools
from typing import Callable, Awaitable, Dict, Optional
from backend.ws.task_manager import task_manager
try:
    from backend.core.metrics import (
        SCHEDULER_QUEUE_DEPTH,
        SCHEDULER_RUNNING,
        SCHEDULER_TASKS_TOTAL,
    )  # type: ignore
except Exception:
    class _No:
        def labels(self, *_, **__):
            return self
        def inc(self, *_):
            pass
        def set(self, *_):
            pass
    SCHEDULER_QUEUE_DEPTH = SCHEDULER_RUNNING = SCHEDULER_TASKS_TOTAL = _No()


class Scheduler:
    """
    简单全局任务调度器（按优先级启动多个 DAG 流程）。
    - 使用 asyncio.PriorityQueue
    - 通过 Semaphore 控制并发管道数（pipeline 级并发）
    - 支持更新优先级：通过追加新条目并标记旧条目为取消
    """
    def __init__(self, max_parallel: int = 2):
        self._pq: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._started = False
        self._sema = asyncio.Semaphore(max_parallel)
        self._max_parallel = max_parallel
        self._counter = itertools.count()
        self._cancelled: set[str] = set()
        self._queued_entries: Dict[str, tuple] = {}  # task_id -> (priority, count)

    async def ensure_started(self):
        if not self._started:
            self._started = True
            asyncio.create_task(self._worker())

    async def submit(self, task_id: str, priority: int, coro_factory: Callable[[], Awaitable[None]]):
        await self.ensure_started()
        cnt = next(self._counter)
        await self._pq.put((priority, cnt, task_id, coro_factory))
        self._queued_entries[task_id] = (priority, cnt)
        # 记录排队状态
        task_manager.set_task_queue_status(task_id, "queued", priority)
        try:
            SCHEDULER_QUEUE_DEPTH.set(self._pq.qsize())  # type: ignore
            SCHEDULER_TASKS_TOTAL.labels(status="queued").inc()
        except Exception:
            pass

    async def update_priority(self, task_id: str, new_priority: int):
        # 标记旧条目取消，重新入队
        self._cancelled.add(task_id)
        cnt = next(self._counter)
        await self._pq.put((new_priority, cnt, task_id, None))  # 先占坑，实际执行时从 task_manager 取 coro
        self._queued_entries[task_id] = (new_priority, cnt)
        task_manager.set_task_queue_status(task_id, "queued", new_priority)
        try:
            SCHEDULER_QUEUE_DEPTH.set(self._pq.qsize())  # type: ignore
            SCHEDULER_TASKS_TOTAL.labels(status="queued").inc()
        except Exception:
            pass

    async def _worker(self):
        while True:
            priority, cnt, task_id, coro_factory = await self._pq.get()
            if task_id in self._cancelled:
                # 丢弃旧条目
                self._cancelled.discard(task_id)
                try:
                    SCHEDULER_QUEUE_DEPTH.set(self._pq.qsize())  # type: ignore
                except Exception:
                    pass
                continue
            # 从 task_manager 获取挂载的执行函数
            if coro_factory is None:
                coro_factory = task_manager.get_task_coro(task_id)
                if coro_factory is None:
                    try:
                        SCHEDULER_QUEUE_DEPTH.set(self._pq.qsize())  # type: ignore
                    except Exception:
                        pass
                    continue
            try:
                # 刚从队列取出，更新队列深度
                SCHEDULER_QUEUE_DEPTH.set(self._pq.qsize())  # type: ignore
            except Exception:
                pass
            async with self._sema:
                task_manager.set_task_queue_status(task_id, "running", priority)
                try:
                    SCHEDULER_RUNNING.inc()
                    SCHEDULER_TASKS_TOTAL.labels(status="running").inc()
                except Exception:
                    pass
                try:
                    await coro_factory()
                finally:
                    task_manager.set_task_queue_status(task_id, "done", priority)
                    try:
                        # 任务结束，减少运行中计数
                        SCHEDULER_RUNNING.inc(-1)
                        SCHEDULER_TASKS_TOTAL.labels(status="done").inc()
                    except Exception:
                        pass

    def get_config(self) -> dict:
        return {"max_concurrent_pipelines": self._max_parallel}

    def set_max_parallel(self, n: int):
        if n < 1:
            n = 1
        # 更新 Semaphore 容量：创建新的信号量替换（简化实现，针对新调度生效）
        self._sema = asyncio.Semaphore(n)
        self._max_parallel = n


scheduler = Scheduler()
