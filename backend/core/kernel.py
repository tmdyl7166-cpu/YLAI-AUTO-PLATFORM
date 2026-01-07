import asyncio
import importlib
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import json
import requests
import hashlib
from .registry import registry
from .logger import logger
from backend.core.pipeline import Pipeline
from backend.core.task import Task
from backend.core.policy import GlobalPolicy
import importlib
import time

def execute_node(node, ws_send=None):
    """
    node: {id, script, params, depends_on}
    ws_send: WebSocket 发送函数，可选
    """
    node_id = node["id"]
    script_name = node["script"]
    params = node.get("params", {})
    
    try:
        module = importlib.import_module(f"scripts.spider.{script_name}")
        start_time = time.time()
        
        # 模拟逐秒状态推送
        for sec in range(1, 4):
            if ws_send:
                ws_send(node_id, {"status":"running", "elapsed":sec})
            time.sleep(1)
        
        result = module.run(params)
        node["status"] = result.get("status", "success")
        node["data"] = result.get("data", None)
        
        if ws_send:
            ws_send(node_id, {"status": node["status"], "elapsed": time.time() - start_time})
        
    except Exception as e:
        node["status"] = "failed"
        node["error"] = str(e)
        if ws_send:
            ws_send(node_id, {"status":"failed","error":str(e)})


class Kernel:
    def __init__(self):
        self.registry = registry
        logger.info("🚀 后端内核初始化...")
        self._cache: dict[str, dict] = {}

    def load_scripts(self):
        self.registry.auto_register("backend.scripts")
        logger.info(f"✅ 已注册脚本: {', '.join(self.registry.list_all())}")

    def run(self, name: str, **kwargs):
        logger.info(f"▶️ 启动脚本: {name}")
        # 全局策略接入：根据等级调整参数与安全行为
        level = GlobalPolicy.level()
        params = dict(kwargs)
        if level == 0:
            # SAFE：严格速率与禁用代理/AI 修复
            params["delay"] = max(params.get("delay", 0), GlobalPolicy.request_interval_ms() / 1000.0)
            params["use_proxy"] = False
            params["_ai_fix"] = False
        elif level >= 2:
            # STRESS/RESEARCH：提升并发上限（由脚本自行消费）
            params["concurrency"] = GlobalPolicy.max_concurrency()
        if not GlobalPolicy.allow_ai_fix():
            params["_ai_fix"] = False
        script = self.registry.get(name)
        return script.run(**params)

    async def run_async(self, name: str, **kwargs):
        """
        异步封装：在线程池中执行同步的 run，便于并发场景使用。
        用于 DAG 并发引擎或需要 asyncio 兼容时。
        """
        return await asyncio.to_thread(self.run, name, **kwargs)

    def list_scripts(self):
        return self.registry.list_all()

    # === AI 自动参数生成（最小实现） ===
    def ai_generate_params(self, node_id: str, error_msg: str, task_state: dict, base_params: dict | None = None) -> dict:
        """
        基于失败信息与上下文，让本地 AI 生成新的参数。
        - 使用字段白名单：仅允许修改 base_params 中已存在的键。
        - 安全返回：若 AI 响应不可解析或不合理，则返回空字典。
        """
        base = os.environ.get("OLLAMA_URL", os.environ.get("AI_URL", "http://127.0.0.1:11434")).rstrip("/")
        ai_url = f"{base}/api/generate"
        model = os.environ.get("AI_MODEL", "deepseek-r1:8b")
        base_params = dict(base_params or {})

        # 压缩上下文，避免过大
        context = {
            "node_id": node_id,
            "error": str(error_msg)[:2000],
            "base_params": base_params,
        }
        prompt = (
            "你是参数调优助手。\n"
            "根据错误信息与当前参数，给出一个仅包含需要修改键的 JSON 对象。\n"
            "要求：\n"
            "- 只输出 JSON，不要任何解释。\n"
            "- 仅包含允许变更的字段（与 base_params 同名键）。\n"
            "- 不要新增结构性字段。\n"
            f"上下文: {json.dumps(context, ensure_ascii=False)}\n"
            "输出示例：{\"timeout\": 30, \"retry\": 1}"
        )

        try:
            resp = requests.post(
                ai_url,
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            text = (data.get("response") or "").strip()
            # 兼容思维链，提取 JSON 片段
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start:end+1]
            suggested = json.loads(text)
            if not isinstance(suggested, dict):
                return {}
            # 白名单：仅允许修改 base_params 里存在的键
            cleaned = {}
            for k, v in suggested.items():
                if k in base_params:
                    # 基础类型限制，避免可执行对象
                    if isinstance(v, (str, int, float, bool)) or v is None or isinstance(v, (list, dict)):
                        cleaned[k] = v
            return cleaned
        except Exception as e:
            logger.error(f"AI 生成参数失败: {e}")
            return {}

    # === 内存缓存（最小实现） ===
    @staticmethod
    def _hash_params(script: str, params: dict) -> str:
        try:
            dump = json.dumps({"script": script, "params": params}, ensure_ascii=False, sort_keys=True)
        except Exception:
            dump = f"{script}:{str(params)}"
        return hashlib.sha256(dump.encode("utf-8")).hexdigest()

    def try_cache(self, script: str, params: dict) -> dict | None:
        # 可通过 params._cache = False 关闭缓存
        if params.get("_cache") is False:
            return None
        key = self._hash_params(script, {k: v for k, v in params.items() if not k.startswith("_")})
        return self._cache.get(key)

    def save_cache(self, script: str, params: dict, result: dict):
        if params.get("_cache") is False:
            return
        key = self._hash_params(script, {k: v for k, v in params.items() if not k.startswith("_")})
        self._cache[key] = result
    def run_pipeline(self, task_list: list):
        pipeline = Pipeline(self)

        for item in task_list:
            task = Task(
                script=item["script"],
                params=item.get("params", {})
            )
            pipeline.add_task(task)

        return pipeline.run()


# ===== 简易 DAG 执行（示例版） =====

def execute_node(node: dict, ws_send=None):
    node_id = node["id"]
    script_name = node["script"]
    params = node.get("params", {})
    category = node.get("category", "spider")  # spider/ai/process

    try:
        module = importlib.import_module(f"backend.scripts.{category}.{script_name}")
        start_time = time.time()
        if ws_send:
            ws_send(node_id, {"status": "running", "elapsed": 0})
        result = module.run(params)
        node["status"] = result.get("status", "success")
        node["data"] = result.get("data", None)
        if ws_send:
            ws_send(node_id, {"status": node["status"], "elapsed": time.time() - start_time})
    except Exception as e:
        node["status"] = "failed"
        node["error"] = str(e)
        if ws_send:
            ws_send(node_id, {"status": "failed", "error": str(e)})


def run_pipeline(nodes: list[dict], max_workers: int = 4, ws_send=None):
    """
    简易并行 DAG 执行（不处理循环依赖），在可运行时调度节点到线程池。
    """
    # 跟踪依赖与状态
    depends = {n["id"]: set(n.get("depends_on", [])) for n in nodes}
    node_map = {n["id"]: n for n in nodes}

    executor = ThreadPoolExecutor(max_workers=max_workers)
    in_progress = {}
    finished = set()

    def submit_ready():
        for nid, deps in list(depends.items()):
            if nid in finished or nid in in_progress:
                continue
            if not deps:  # 无依赖，或依赖已完成
                if ws_send:
                    ws_send(nid, {"status": "queued"})
                future = executor.submit(execute_node, node_map[nid], ws_send)
                in_progress[nid] = future

    # 初始标记等待状态
    for nid, d in depends.items():
        if d and ws_send:
            ws_send(nid, {"status": "waiting"})

    submit_ready()

    while len(finished) < len(nodes):
        done = [nid for nid, fut in in_progress.items() if fut.done()]
        for nid in done:
            _ = in_progress.pop(nid)
            finished.add(nid)
            # 解除其他节点对它的依赖
            for dn in depends.values():
                dn.discard(nid)
        if done:
            submit_ready()
        else:
            # 避免空转占用 CPU
            time.sleep(0.05)

    executor.shutdown(wait=True)
    return nodes
