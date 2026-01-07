import os
import requests
import json
import time
from backend.core.kernel import Kernel
from typing import Optional, Dict, Any

MODEL = os.environ.get("AI_MODEL", "deepseek-r1:8b")

kernel = Kernel()
kernel.load_scripts()


def _resolve_ai_endpoint() -> str:
    env = os.getenv("AI_ENDPOINT")
    if env:
        return env.rstrip("/") + "/api/generate" if "/api/" not in env else env
    # Prefer host-mapped 11500 (compose), then defaults
    ports = [11500, 11434, 11435, 9000, 37683, 33427]
    for p in ports:
        url = f"http://127.0.0.1:{p}/api/generate"
        try:
            r = requests.post(url, json={"model": "deepseek-r1:8b", "prompt": "ping", "stream": False}, timeout=1.5)
            if r.status_code == 200:
                return url
        except Exception:
            continue
    return "http://127.0.0.1:11434/api/generate"


def ask_ai_pipeline(prompt: str, model: str = MODEL) -> Dict[str, Any]:
    endpoint = _resolve_ai_endpoint()
    try:
        start = time.time()
        r = requests.post(endpoint, json={"model": model, "prompt": prompt, "stream": False}, timeout=10)
        r.raise_for_status()
        data = r.json()
        latency_ms = int((time.time() - start) * 1000)
        return {"status": "success", "endpoint": endpoint, "latency_ms": latency_ms, "data": data}
    except Exception as e:
        return {"status": "error", "endpoint": endpoint, "error": str(e)}


def run_ai_task(prompt: str):
    return ask_ai_pipeline(prompt)


def optimize_error(error_text: str, context: Optional[Dict[str, Any]] = None):
    context = context or {}
    prompt = (
        "你是代码修复助手。只返回JSON，不要解释。\n"
        "请分析如下错误并给出修复建议：\n"
        f"错误: {error_text}\n"
        f"上下文: {json.dumps(context or {}, ensure_ascii=False)}\n"
        "返回格式：{\n"
        "  \"intent\": \"error_fix\",\n"
        "  \"summary\": \"...\",\n"
        "  \"causes\": [\"...\"],\n"
        "  \"fixes\": [{\n"
        "    \"title\": \"...\",\n"
        "    \"steps\": [\"...\"],\n"
        "    \"files\": [\"...\"],\n"
        "    \"risk\": \"low\"\n"
        "  }]\n"
        "}"
    )
    return ask_ai_pipeline(prompt)
