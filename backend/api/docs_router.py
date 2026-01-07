from fastapi import APIRouter, HTTPException, Depends, Body
from backend.api.auth import require_perm
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List, Dict, Any

docs_router = APIRouter()

# 项目根目录的 docs 目录：backend/ 的上一级为项目根
DOCS_DIR = (Path(__file__).resolve().parent.parent.parent / "docs").resolve()
PAGES_DIR = (Path(__file__).resolve().parent.parent.parent / "frontend" / "pages").resolve()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.resolve()


@docs_router.get("/api/docs/{task_id}")
async def get_task_doc(task_id: str, _auth=Depends(require_perm("view"))):
    file_path = (DOCS_DIR / f"{task_id}.md").resolve()
    try:
        # 安全检查：确保不越界到 docs 目录之外
        file_path.relative_to(DOCS_DIR)
    except Exception:
        raise HTTPException(status_code=400, detail="非法路径")

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文档不存在")

    return FileResponse(str(file_path), media_type="text/markdown")


def _safe_resolve(rel_path: str) -> Path:
    """安全解析相对路径到项目根，并限制写入到受控目录（docs/ 与 frontend/pages/）。"""
    p = (PROJECT_ROOT / rel_path).resolve()
    try:
        # 允许写入 docs/ 或 frontend/pages/
        if p.is_relative_to(DOCS_DIR) or p.is_relative_to(PAGES_DIR):
            return p
    except AttributeError:
        # Python < 3.9 无 is_relative_to，使用 try/except relative_to
        try:
            p.relative_to(DOCS_DIR)
            return p
        except Exception:
            pass
        try:
            p.relative_to(PAGES_DIR)
            return p
        except Exception:
            pass
    raise HTTPException(status_code=400, detail="非法写入路径")


@docs_router.post("/api/docs/sync")
async def sync_doc(
    payload: Dict[str, Any] = Body(...),
    _auth=Depends(require_perm("edit")),
):
    """
    源→镜像同步：将源文件内容写入目标文件。
    请求体: { from: "docs/统一接口映射表.md", to: "frontend/pages/统一接口映射表.md", content: "..." }
    """
    src = str(payload.get("from") or "").strip()
    dst = str(payload.get("to") or "").strip()
    content = str(payload.get("content") or "")
    if not src or not dst:
        raise HTTPException(status_code=400, detail="缺少 from/to")
    # 校验源文件必须位于 docs/
    src_path = (PROJECT_ROOT / src).resolve()
    try:
        src_path.relative_to(DOCS_DIR)
    except Exception:
        raise HTTPException(status_code=400, detail="源文件不在 docs 目录")
    # 目标路径受控
    dst_path = _safe_resolve(dst)
    # 写入目标
    dst_path.parent.mkdir(parents=True, exist_ok=True)
    dst_path.write_text(content, encoding="utf-8")
    return {"code": 0, "data": {"to": str(dst_path), "bytes": len(content.encode("utf-8"))}}


@docs_router.post("/api/docs/propose")
async def propose_docs(
    payload: Dict[str, Any] = Body(...),
    _auth=Depends(require_perm("edit")),
):
    """
    前端提议双向同步：将多文件内容以提议形式保存到临时目录，待审核合并。
    请求体: { proposal: "sync-md", files:[{ path:"docs/xx.md", content:"..." }, ...], message:"..." }
    写入到 docs/proposals/{ts}/ 下，文件名与相对路径一致。
    """
    files: List[Dict[str, Any]] = payload.get("files") or []
    message: str = str(payload.get("message") or "")
    if not files:
        raise HTTPException(status_code=400, detail="缺少 files")
    import time
    ts = int(time.time())
    out_dir = (DOCS_DIR / "proposals" / str(ts)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for f in files:
        path = str(f.get("path") or "").strip()
        content = str(f.get("content") or "")
        if not path:
            continue
        # 仅允许提议 docs/ 或 frontend/pages/ 路径
        try:
            target = _safe_resolve(path)
        except HTTPException:
            # 将非法路径记录为忽略项
            written.append({"path": path, "ignored": True})
            continue
        # 在 proposals 目录中镜像保存（不直接覆盖真实文件）
        mirror = (out_dir / path.replace("\\", "/")).resolve()
        mirror.parent.mkdir(parents=True, exist_ok=True)
        mirror.write_text(content, encoding="utf-8")
        written.append({"path": path, "saved": str(mirror)})
    # 保存提议说明
    (out_dir / "README.txt").write_text(message or "", encoding="utf-8")
    return {"code": 0, "data": {"dir": str(out_dir), "written": written}}
