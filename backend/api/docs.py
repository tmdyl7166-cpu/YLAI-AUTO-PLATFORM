from fastapi import APIRouter
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

docs_router = APIRouter()

# 项目根的 docs 目录
DOCS_DIR = Path(__file__).resolve().parents[1] / "docs"

@docs_router.get("/api/docs/{task_id}")
async def get_task_doc(task_id: str):
    # 允许直接传入诸如 task_1、task-1、1 等形式，统一映射到 task_*.md
    normalized = task_id
    if not normalized.endswith(".md"):
        if not normalized.startswith("task_"):
            # 尝试补全前缀
            normalized = f"task_{normalized}"
        normalized = f"{normalized}.md"
    file_path = DOCS_DIR / normalized
    if not file_path.exists():
        return JSONResponse({"error": "文档不存在"}, status_code=404)
    return FileResponse(file_path, media_type="text/markdown")
