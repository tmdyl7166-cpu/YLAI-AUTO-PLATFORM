import asyncio
import time
from typing import List, Dict, Any

from backend.core.task import Task, Node
try:
    from backend.core.metrics import (
        PIPELINE_NODE_SECONDS,
        PIPELINE_NODE_FAILURES,
        PIPELINE_RUNS_OVERALL,
    )  # type: ignore
except Exception:
    class _No:
        def labels(self, *_, **__):
            return self
        def observe(self, *_):
            pass
        def inc(self, *_):
            pass
    PIPELINE_NODE_SECONDS = PIPELINE_NODE_FAILURES = PIPELINE_RUNS_OVERALL = _No()
from backend.core.logger import logger


class Pipeline:
    """
    多步骤任务顺序流水线执行器（串行）
    使用方式：
      p = Pipeline(kernel)
      p.add_task(Task(script="demo", params={...}))
      result = p.run()
    """

    def __init__(self, kernel):
        self.kernel = kernel
        self.tasks: List[Task] = []

    def add_task(self, task: Task):
        self.tasks.append(task)

    def run(self) -> Dict[str, Any]:
        logger.info("🚀 启动任务流水线（串行）")
        result_cache = None

        for index, task in enumerate(self.tasks, start=1):
            logger.info(f"➡️ 执行第 {index} 步：{task.script}")

            try:
                # 把上一个任务结果传给下一个
                params = dict(task.params or {})
                if result_cache is not None:
                    params["prev_result"] = result_cache

                result_cache = self.kernel.run(task.script, **params)

            except Exception as e:
                logger.error(f"❌ 流水线中断于步骤 {index}: {str(e)}")
                return {
                    "status": "failed",
                    "step": index,
                    "error": str(e)
                }

        logger.info("✅ 流水线全部完成")
        return {
            "status": "success",
            "result": result_cache
        }


class DAGPipeline:
    """
    DAG 并行流水线引擎（基于 asyncio）
    使用方式:
      pipeline = DAGPipeline(kernel)
      await pipeline.run(nodes, max_concurrency=4, node_timeout=300)
    """

    def __init__(self, kernel, max_concurrency: int = 4):
        self.kernel = kernel
        self.max_concurrency = max_concurrency

    def validate(self, nodes: List[Node], registered_scripts: List[str]) -> Dict[str, Any]:
        """
        静态校验：
         - id 唯一
         - script 已注册
         - depends_on 中引用存在
         - 无环检测（拓扑检查）
        返回 { ok: bool, errors: [str] }
        """
        errors = []
        ids = [n.id for n in nodes]
        if len(ids) != len(set(ids)):
            errors.append("节点 id 不唯一")

        id_set = set(ids)
        for n in nodes:
            if n.script not in registered_scripts:
                errors.append(f"节点 {n.id} 使用了未注册脚本: {n.script}")
            for dep in n.depends_on:
                if dep not in id_set:
                    errors.append(f"节点 {n.id} 依赖了不存在的节点: {dep}")

        # 无环检测: Kahn 拓扑法
        indeg = {nid: 0 for nid in ids}
        graph = {nid: [] for nid in ids}
        for n in nodes:
            for d in n.depends_on:
                graph[d].append(n.id)
                indeg[n.id] += 1

        q = [nid for nid, d in indeg.items() if d == 0]
        visited = 0
        while q:
            cur = q.pop()
            visited += 1
            for nei in graph[cur]:
                indeg[nei] -= 1
                if indeg[nei] == 0:
                    q.append(nei)
        if visited != len(ids):
            errors.append("存在环依赖或依赖无法解析（非 DAG）")

        return {"ok": len(errors) == 0, "errors": errors}

    async def run(self, nodes: List[Node], max_concurrency: int = None, node_timeout: int = None) -> Dict[str, Any]:
        """
        执行 DAG：
        - nodes: Node 列表（任意顺序）
        - max_concurrency: 限制并发（None 则使用 self.max_concurrency）
        - node_timeout: 单节点超时（秒），None 表示不限制
        返回：
        {
          "status": "success"|"failed",
          "nodes": {
             "<node_id>": {"status": "success"/"failed"/"skipped"/"cancelled", "result": ..., "error": ..., "duration": float}
          },
          "order": [完成顺序的 node_id 列表]
        }
        """
        if max_concurrency is None:
            max_concurrency = self.max_concurrency

        # internal maps
        id_to_node = {n.id: n for n in nodes}
        dependents = {n.id: [] for n in nodes}
        remaining_deps = {n.id: len(n.depends_on) for n in nodes}

        for n in nodes:
            for dep in n.depends_on:
                dependents[dep].append(n.id)

        semaphore = asyncio.Semaphore(max_concurrency)
        loop = asyncio.get_event_loop()

        results: Dict[str, Dict[str, Any]] = {}
        completed_order: List[str] = []
        running_tasks: Dict[str, asyncio.Task] = {}

        # upstream aggregation helper
        def gather_upstream_results(node_id: str) -> Dict[str, Any]:
            # collect results of dependencies: {dep_id: results[dep_id]["result"]}
            data: Dict[str, Any] = {}
            for dep in id_to_node[node_id].depends_on:
                # include full result object to be flexible
                data[dep] = results.get(dep, {}).get("result")
            return data

        def eval_condition(expr: Any, context: Dict[str, Any]) -> bool:
            if expr in (None, "", True):
                return True
            if expr is False:
                return False
            try:
                local_ctx = {**context, "null": None, "None": None, "true": True, "false": False}
                return bool(eval(str(expr), {"__builtins__": {}}, local_ctx))
            except Exception:
                return True

        async def exec_node(node_id: str):
            node = id_to_node[node_id]
            await semaphore.acquire()
            start = time.time()
            logger.info(f"开始执行节点 {node_id} -> 脚本 {node.script}")
            try:
                # prepare params copy and inject upstream results
                params = dict(node.params or {})
                params["_upstream_results"] = gather_upstream_results(node_id)

                # 条件判定：不满足则跳过
                cond_ok = eval_condition(getattr(node, "condition", None), {"up": params["_upstream_results"], "params": params})
                if not cond_ok:
                    duration = 0.0
                    results[node_id] = {"status": "skipped", "result": None, "error": None, "duration": duration}
                    logger.info(f"节点 {node_id} 条件不满足，跳过执行")
                else:
                    # 缓存命中则直接返回
                    cached = self.kernel.try_cache(node.script, params)
                    if cached is not None:
                        duration = time.time() - start
                        results[node_id] = {"status": "success", "result": cached, "error": None, "duration": duration, "cached": True}
                        logger.info(f"节点 {node_id} 缓存命中 (t={duration:.2f}s)")
                        try:
                            PIPELINE_NODE_SECONDS.labels(mode="async", script=node.script).observe(duration)
                        except Exception:
                            pass
                    else:
                    # run kernel.run in threadpool (kernel.run 是同步)
                        coro = loop.run_in_executor(None, self.kernel.run, node.script, **params)
                        if node_timeout:
                            res = await asyncio.wait_for(coro, timeout=node_timeout)
                        else:
                            res = await coro

                        duration = time.time() - start
                        results[node_id] = {"status": "success", "result": res, "error": None, "duration": duration}
                        self.kernel.save_cache(node.script, params, res)
                        logger.info(f"节点 {node_id} 执行成功 (t={duration:.2f}s)")
                        try:
                            PIPELINE_NODE_SECONDS.labels(mode="async", script=node.script).observe(duration)
                        except Exception:
                            pass

            except asyncio.CancelledError:
                duration = time.time() - start
                results[node_id] = {"status": "cancelled", "result": None, "error": "cancelled", "duration": duration}
                logger.error(f"节点 {node_id} 被取消")
            except Exception as e:
                duration = time.time() - start
                results[node_id] = {"status": "failed", "result": None, "error": str(e), "duration": duration}
                logger.error(f"节点 {node_id} 执行失败: {e}")
                try:
                    PIPELINE_NODE_FAILURES.labels(mode="async", script=node.script).inc()
                except Exception:
                    pass
            finally:
                semaphore.release()

            # mark completed
            completed_order.append(node_id)

            # schedule dependents if ready
            for depn in dependents.get(node_id, []):
                remaining_deps[depn] -= 1
                # if any predecessor failed, we mark dependent as blocked (do not schedule)
                blocked = False
                for p in id_to_node[depn].depends_on:
                    if results.get(p, {}).get("status") == "failed":
                        blocked = True
                        break
                if blocked:
                    # mark this node as blocked/skipped
                    results[depn] = {"status": "skipped", "result": None, "error": f"依赖节点失败，节点 {depn} 被跳过", "duration": 0.0}
                    completed_order.append(depn)
                    # propagate skip to its dependents too
                    for nextn in dependents.get(depn, []):
                        remaining_deps[nextn] -= 1
                    continue

                if remaining_deps[depn] == 0 and depn not in running_tasks and results.get(depn) is None:
                    # schedule execution
                    running_tasks[depn] = asyncio.create_task(exec_node(depn))

        # initially schedule all nodes with remaining_deps == 0
        for nid, cnt in list(remaining_deps.items()):
            if cnt == 0:
                running_tasks[nid] = asyncio.create_task(exec_node(nid))

        # wait for all running tasks to complete
        if running_tasks:
            await asyncio.gather(*running_tasks.values())

        # determine overall status
        overall = "success"
        for _nid, r in results.items():
            if r["status"] == "failed":
                overall = "failed"
                break

        # record overall (async) run status
        try:
            PIPELINE_RUNS_OVERALL.labels(mode="async", status=overall).inc()
        except Exception:
            pass

        return {
            "status": overall,
            "nodes": results,
            "order": completed_order
        }
 
