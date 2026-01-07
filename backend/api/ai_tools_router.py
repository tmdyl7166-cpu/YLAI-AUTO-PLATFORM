from fastapi import APIRouter
from pathlib import Path
from typing import List

from backend.scripts.ai.orchestrator import run_pipeline_on_file, run_pipeline_on_dirs
from backend.scripts.ai.config import WATCH_DIR

router = APIRouter(prefix="/api/ai-tools", tags=["ai-tools"])

@router.post("/file")
def optimize_file(payload: dict):
    file = payload.get("file")
    auto_approve = bool(payload.get("auto_approve", True))
    if not file:
        return {"status": "error", "msg": "file required"}
    p = Path(file)
    res = run_pipeline_on_file(p, auto_fix=True, auto_approve=auto_approve)
    return {"status": "ok", "result": res}

@router.post("/trigger")
def trigger_dirs(payload: dict):
    auto_approve = bool(payload.get("auto_approve", True))
    dirs: List[Path] = [WATCH_DIR]
    res = run_pipeline_on_dirs(dirs, auto_fix=True)
    return {"status": "ok", "result": res}
