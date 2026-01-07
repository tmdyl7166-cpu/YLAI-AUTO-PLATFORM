
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import requests
import os
from pathlib import Path


app = FastAPI()


# 允许跨域，便于前端直接调用
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434/api/generate")
ALLOWED_MODELS = {"qwen2.5:3b", "llama3.1:8b", "gpt-oss:20b"}


INDEX_FILE = Path("/app/index.html")


class GenerateRequest(BaseModel):
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 512


@app.get("/")
def root():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return {"status": "ok", "result": "Ollama Proxy API"}


@app.get("/index.html")
def index_html():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return {"status": "error", "result": "index.html 未找到"}


@app.get("/models")
def get_models():
    return JSONResponse({"status": "success", "result": sorted(list(ALLOWED_MODELS))})


@app.get("/health")
def health():
    try:
        tags_url = OLLAMA_URL.replace("/generate", "/tags")
        resp = requests.get(tags_url, timeout=5)
        resp.raise_for_status()
        return {"status": "success", "result": resp.json()}
    except Exception as e:
        return {"status": "error", "result": str(e)}


@app.post("/generate")
async def generate(req: GenerateRequest):
    if req.model not in ALLOWED_MODELS:
        return {"status": "error", "result": f"模型 {req.model} 不允许"}
    payload = {
        "model": req.model,
        "prompt": req.prompt,
        "stream": False,
        "options": {
            "temperature": req.temperature,
            "num_predict": req.max_tokens
        }
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        data = resp.json()
        result = data.get("response") or data.get("result") or str(data)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "result": str(e)}
