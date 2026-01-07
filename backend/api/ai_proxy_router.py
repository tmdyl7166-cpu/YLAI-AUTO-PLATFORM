from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import requests

router = APIRouter(prefix="/api/ai-proxy", tags=["ai-proxy"])

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate")
ALLOWED_MODELS = {"qwen2.5:3b", "llama3.1:8b", "gpt-oss:20b"}

class GenerateRequest(BaseModel):
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 512

@router.get("/models")
def get_models():
    return JSONResponse({"status": "success", "result": sorted(list(ALLOWED_MODELS))})

@router.get("/health")
def health():
    try:
        tags_url = OLLAMA_URL.replace("/generate", "/tags")
        resp = requests.get(tags_url, timeout=5)
        resp.raise_for_status()
        return {"status": "success", "result": resp.json()}
    except Exception as e:
        return {"status": "error", "result": str(e)}

@router.post("/generate")
def generate(req: GenerateRequest):
    if req.model not in ALLOWED_MODELS:
        return {"status": "error", "result": f"模型 {req.model} 不允许"}
    payload = {
        "model": req.model,
        "prompt": req.prompt,
        "stream": False,
        "options": {"temperature": req.temperature, "num_predict": req.max_tokens},
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("response") or data.get("result") or str(data)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}
