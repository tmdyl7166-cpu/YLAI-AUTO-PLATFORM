# 迁移自 ai-docker/ai_router.py 的路由适配入口（占位）
# 若需与 backend/app.py 深度集成，请在此实现 AIRouter/OllamaClient 等类，或直接复用现有桥接。

from typing import Any, Dict
import os
import requests

class OllamaClient:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")

    def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url.rstrip('/')}/api/generate"
        try:
            r = requests.post(url, json=payload, timeout=120)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            return {"error": str(e)}

class AIRouter:
    def __init__(self, client: OllamaClient):
        self.client = client

    def run_pipeline(self, prompt: str) -> Dict[str, Any]:
        payload = {"model": os.getenv("AI_MODEL", "gpt-oss:20b"), "prompt": prompt, "stream": False}
        return self.client.generate(payload)
