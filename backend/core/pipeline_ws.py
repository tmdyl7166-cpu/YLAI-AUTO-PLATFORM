import asyncio, time, datetime, uuid
from typing import List, Any, Dict
from backend.core.task import Node
try:
    from backend.core.metrics import PIPELINE_NODE_SECONDS, PIPELINE_NODE_FAILURES, PIPELINE_RUNS_OVERALL, PIPELINE_NODE_RETRIES  # type: ignore
except Exception:
    class _No:
        def labels(self, *_, **__):
            return self
        def observe(self, *_):
            pass
        def inc(self, *_):
            pass
    PIPELINE_NODE_SECONDS = PIPELINE_NODE_FAILURES = PIPELINE_RUNS_OVERALL = PIPELINE_NODE_RETRIES = _No()
try:
    from backend.core.metrics import PIPELINE_NODE_SECONDS, PIPELINE_NODE_FAILURES, PIPELINE_RUNS_OVERALL  # type: ignore
except Exception:
    class _No:
        def labels(self, *_, **__):
            return self
        def observe(self, *_):
            pass
        def inc(self, *_):
            pass
    PIPELINE_NODE_SECONDS = PIPELINE_NODE_FAILURES = PIPELINE_RUNS_OVERALL = _No()
from backend.ws.manager import ws_manager
from backend.ws.task_manager import task_manager
from backend.ws.scheduler import scheduler

MAX_RETRY = 2  # AI 自动重试次数
BASE_BACKOFF = 0.5  # 秒，指数退避基础值

def is_retryable_error(err: Exception) -> bool:
    """粗略判断是否可重试：网络/超时等"""
    msg = str(err).lower()
    for key in ("timeout", "tempor", "connection", "rate limit", "429"):
        if key in msg:
            return True
    return False

class WSDAGPipeline:
    def __init__(self, kernel):
        self.kernel = kernel

    async def run(self, nodes: List[Node], max_concurrency=4, priority: int = 100):
        task_id = str(uuid.uuid4())
        task_manager.init_task(task_id, nodes, priority=priority)
        # 将执行函数注册给 scheduler
        task_manager.set_task_coro(task_id, lambda: self._execute(task_id, nodes, max_concurrency))
        # 入队，按优先级调度
        await scheduler.submit(task_id, priority, lambda: self._execute(task_id, nodes, max_concurrency))
        return task_id

    async def _execute(self, task_id: str, nodes: List[Node], max_concurrency: int):
        # 广播流水线启动事件（真正开始执行时）
        try:
            PIPELINE_RUNS_OVERALL.labels(mode="ws", status="start").inc()
        except Exception:
            pass
        await ws_manager.broadcast(task_id, {"type": "pipeline_start", "task_id": task_id})
        sem = asyncio.Semaphore(max_concurrency)
        loop = asyncio.get_event_loop()
        id_map = {n.id: n for n in nodes}
        deps = {n.id: set(n.depends_on) for n in nodes}

        # 初始化：有依赖的标记为 waiting，无依赖的稍后入队
        for nid, d in deps.items():
            if d:
                task_manager.update_node(task_id, nid, "waiting")
                await ws_manager.broadcast_node_update(task_id, nid)

        def gather_upstream_results(node_id: str) -> Dict[str, Any]:
            st = task_manager.get_task_state(task_id)
            data: Dict[str, Any] = {}
            for dep in id_map[node_id].depends_on:
                data[dep] = st["nodes"][dep]["result"]
            return data

        def eval_condition(expr: Any, context: Dict[str, Any]) -> bool:
            if expr in (None, "", True):
                return True
            if expr is False:
                return False
            try:
                # 极简安全评估，仅暴露 up/params，禁用内建
                local_ctx = {**context, "null": None, "None": None, "true": True, "false": False}
                return bool(eval(str(expr), {"__builtins__": {}}, local_ctx))
            except Exception:
                return True  # 解析出错默认不阻断

        async def exec_node(node_id):
            node = id_map[node_id]
            retries = 0
            while retries <= MAX_RETRY:
                # 条件判定（在入队前）
                up = gather_upstream_results(node_id)
                cond_ok = eval_condition(getattr(node, "condition", None), {"up": up, "params": node.params})
                if not cond_ok:
                    task_manager.update_node(task_id, node_id, "skipped", result=None, error=None, start=None, end=datetime.datetime.now(), elapsed=0.0)
                    await ws_manager.broadcast_node_update(task_id, node_id)
                    break
                # 入队（等待并发许可）
                task_manager.update_node(task_id, node_id, "queued")
                await ws_manager.broadcast_node_update(task_id, node_id)
                async with sem:
                    start_time = datetime.datetime.now()
                    task_manager.update_node(task_id, node_id, "running", start=start_time)
                    asyncio.create_task(track_progress(task_id, node_id, start_time))
                try:
                    # 注入上游结果
                    params = dict(node.params)
                    params["_upstream_results"] = up
                    # 缓存命中：直接返回
                    cached_result = _try_cache("ws", node.script, params)
                    if cached_result is not None:
                        end_time = datetime.datetime.now()
                        task_manager.update_node(task_id, node_id, "success", result=cached_result, end=end_time,
                                                 elapsed=(end_time - start_time).total_seconds())
                        # 标记 cached
                        st = task_manager.get_task_state(task_id)
                        st["nodes"][node_id]["cached"] = True
                        await ws_manager.broadcast_node_update(task_id, node_id)
                        try:
                            PIPELINE_NODE_SECONDS.labels(mode="ws", script=node.script).observe((end_time - start_time).total_seconds())
                        except Exception:
                            pass
                        break

                    # 执行节点
                    result = await loop.run_in_executor(None, self.kernel.run, node.script, **params)
                    end_time = datetime.datetime.now()
                    task_manager.update_node(task_id, node_id, "success", result=result, end=end_time,
                                             elapsed=(end_time - start_time).total_seconds())
                    _save_cache("ws", node.script, params, result)
                    await ws_manager.broadcast_node_update(task_id, node_id)
                    try:
                        PIPELINE_NODE_SECONDS.labels(mode="ws", script=node.script).observe((end_time - start_time).total_seconds())
                    except Exception:
                        pass
                    break
                except Exception as e:
                    end_time = datetime.datetime.now()
                    task_manager.update_node(task_id, node_id, "failed", error=str(e), end=end_time,
                                             elapsed=(end_time - start_time).total_seconds())
                    await ws_manager.broadcast_node_update(task_id, node_id)
                    try:
                        PIPELINE_NODE_FAILURES.labels(mode="ws", script=node.script).inc()
                    except Exception:
                        pass
                    if retries < MAX_RETRY and is_retryable_error(e):
                        retries += 1
                        try:
                            PIPELINE_NODE_RETRIES.labels(mode="ws", script=node.script).inc()
                        except Exception:
                            pass
                        # 指数退避等待
                        try:
                            await asyncio.sleep(BASE_BACKOFF * (2 ** (retries - 1)))
                        except Exception:
                            pass
                        # AI 自动生成新参数
                        params = self.kernel.ai_generate_params(node_id, str(e),
                                                                task_manager.get_task_state(task_id), base_params=node.params)
                        node.params.update(params)
                        # 记录参数变更轨迹
                        st = task_manager.get_task_state(task_id)
                        try:
                            st["nodes"][node_id]["param_history"].append({"retry": retries, "patch": params})
                        except Exception:
                            pass
                    else:
                        break

            # 触发依赖节点
            for nid in deps:
                deps[nid].discard(node_id)
                if not deps[nid] and task_manager.get_task_state(task_id)["nodes"][nid]["status"] == "pending":
                    asyncio.create_task(exec_node(nid))

        # 启动无依赖节点
        for nid, d in deps.items():
            if not d:
                asyncio.create_task(exec_node(nid))

async def track_progress(task_id, node_id, start_time):
    while True:
        node_state = task_manager.get_task_state(task_id)["nodes"][node_id]
        if node_state["status"] in ["success", "failed", "skipped"]:
            break
        elapsed = (datetime.datetime.now() - start_time).total_seconds()
        task_manager.update_node(task_id, node_id, None, elapsed=elapsed)
        await ws_manager.broadcast_node_update(task_id, node_id)
        await asyncio.sleep(1)
