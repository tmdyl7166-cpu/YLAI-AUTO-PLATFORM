from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from backend.core.kernel import Kernel
from backend.ai_bridge import ask_ai_and_run
from backend.core.logger import logger

app = FastAPI()
kernel = Kernel()
kernel.load_scripts()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/modules")
def modules():
    return {
        "code": 0,
        "data": list(kernel.registry.scripts.keys())
    }

@app.post("/api/run")
def run_script(payload: dict):
    name = payload.get("script")
    params = payload.get("params", {})
    result = kernel.run(name, **params)
    return {"code": 0, "data": result}

@app.post("/api/ai")
def ai_control(payload: dict):
    prompt = payload.get("prompt")
    result = ask_ai_and_run(prompt)
    return {"code": 0, "data": result}

@app.get("/api/status")
def status():
    return {
        "code": 0,
        "data": {
            "scripts": list(kernel.registry.scripts.keys()),
            "status": "running"
        }
    }

@app.websocket("/ws/monitor")
async def log_ws(ws: WebSocket):
    await ws.accept()
    while True:
        await ws.send_text("✅ 系统运行正常")
