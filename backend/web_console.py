from fastapi import FastAPI
import threading
import time
import asyncio

# Define FastAPI app before any decorators
app = FastAPI()

trigger_thread = None
trigger_stop = False

# 导入AI协调器
try:
    import sys
    from pathlib import Path
    ROOT = Path(__file__).resolve().parents[1]
    sys.path.append(str(ROOT / 'backend'))
    from backend.scripts.ai_coordinator import AIModelCoordinator
    ai_coordinator = None
except ImportError:
    ai_coordinator = None

async def init_ai_coordinator():
    """初始化AI协调器"""
    global ai_coordinator
    if ai_coordinator is None:
        try:
            ai_coordinator = AIModelCoordinator()
            await ai_coordinator.initialize()
        except Exception as e:
            print(f"AI协调器初始化失败: {e}")
            ai_coordinator = None

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化AI协调器"""
    await init_ai_coordinator()

@app.post("/trigger/schedule")
def trigger_schedule(payload: dict):
    """
    定时自动触发优化。payload: {"interval": 秒, "auto_approve": true/false}
    """
    global trigger_thread, trigger_stop
    interval = payload.get("interval", 3600)
    auto_approve = payload.get("auto_approve", True)
    if trigger_thread and trigger_thread.is_alive():
        return {"status": "error", "msg": "already running"}
    trigger_stop = False
    def loop():
        from orchestrator import run_pipeline_on_dirs
        from config import WATCH_DIRS
        while not trigger_stop:
            result = run_pipeline_on_dirs(WATCH_DIRS, auto_fix=True, auto_approve=auto_approve)
            print("[SCHEDULED TRIGGER] result:", result)
            time.sleep(interval)
    trigger_thread = threading.Thread(target=loop, daemon=True)
    trigger_thread.start()
    return {"status": "ok", "msg": f"scheduled every {interval}s"}

@app.post("/trigger/stop")
def trigger_stop_schedule():
    """停止定时自动触发"""
    global trigger_stop
    trigger_stop = True
    return {"status": "ok", "msg": "stopping..."}

import os
import time as _time
from pathlib import Path as _Path

@app.post("/trigger/onchange")
def trigger_onchange(payload: dict):
    """
    文件变更自动触发优化。payload: {"watch_dir": "./", "interval": 秒, "auto_approve": true/false}
    """
    watch_dir = payload.get("watch_dir", "./")
    interval = payload.get("interval", 5)
    auto_approve = payload.get("auto_approve", True)
    last_mtime = {}
    def scan_files():
        for root, _, files in os.walk(watch_dir):
            for f in files:
                p = os.path.join(root, f)
                try:
                    m = os.path.getmtime(p)
                    if p not in last_mtime or last_mtime[p] != m:
                        last_mtime[p] = m
                        yield p
                except Exception:
                    continue
    def loop():
        from orchestrator import run_pipeline_on_dirs
        from config import WATCH_DIRS
        while True:
            changed = list(scan_files())
            if changed:
                print(f"[ONCHANGE TRIGGER] changed: {changed}")
                run_pipeline_on_dirs(WATCH_DIRS, auto_fix=True, auto_approve=auto_approve)
            _time.sleep(interval)
    t = threading.Thread(target=loop, daemon=True)
    t.start()
    return {"status": "ok", "msg": f"watching {watch_dir} every {interval}s"}

from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "results.json"


@app.get("/results")
def list_results():
    if DATA_FILE.exists():
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    return {"items": []}



@app.post("/approve")
def approve_change(payload: dict):
    """
    Approve a pending change and触发健康检查与部署。
    payload: {"file": "..."}
    """
    from orchestrator import run_pipeline_on_file
    from pathlib import Path
    file = payload.get("file")
    if not file:
        return {"status": "error", "msg": "file required"}
    result = run_pipeline_on_file(Path(file), auto_fix=True, auto_approve=True)
    return {"status": "ok", "result": result}

@app.post("/trigger")
def trigger_pipeline(payload: dict):
    """
    触发全目录自动优化与健康检查。
    payload: {"auto_approve": true/false}
    """
    from orchestrator import run_pipeline_on_dirs
    from config import WATCH_DIRS
    auto_approve = payload.get("auto_approve", True)
    result = run_pipeline_on_dirs(WATCH_DIRS, auto_fix=True, auto_approve=auto_approve)
    return {"status": "ok", "result": result}

@app.get("/ai/status")
async def get_ai_status():
    """
    获取AI模型协调器状态
    """
    if ai_coordinator is None:
        return {"status": "error", "msg": "AI协调器未初始化"}

    try:
        status = await ai_coordinator.run('get_model_status')
        return {
            "status": "ok",
            "models": status.get('models', {}),
            "coordinator_status": "active",
            "model_linkage": {
                "qwen3:8b": "中文内容理解与分析",
                "llama3.1:8b": "任务规划与指令理解",
                "deepseek-r1:8b": "复杂推理与决策制定",
                "gpt-oss:20b": "创意生成与文本优化"
            }
        }
    except Exception as e:
        return {"status": "error", "msg": f"获取AI状态失败: {e}"}

@app.post("/ai/analyze")
async def ai_analyze_content(payload: dict):
    """
    使用AI模型分析内容
    payload: {"content": "要分析的内容", "task_type": "analysis|planning|reasoning|generation"}
    """
    if ai_coordinator is None:
        return {"status": "error", "msg": "AI协调器未初始化"}

    content = payload.get("content", "")
    task_type = payload.get("task_type", "analysis")

    try:
        result = await ai_coordinator.run(task_type, content=content)
        return {"status": "ok", "result": result}
    except Exception as e:
        return {"status": "error", "msg": f"AI分析失败: {e}"}

@app.get("/ai/workflow")
async def get_ai_workflow():
    """
    获取AI工作流配置
    """
    if ai_coordinator is None:
        return {"status": "error", "msg": "AI协调器未初始化"}

    try:
        workflow = await ai_coordinator.run('get_workflow_config')
        return {"status": "ok", "workflow": workflow}
    except Exception as e:
        return {"status": "error", "msg": f"获取工作流配置失败: {e}"}
