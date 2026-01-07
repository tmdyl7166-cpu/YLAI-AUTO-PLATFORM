from fastapi import APIRouter
from typing import Any, Dict, Optional, List
import json
import os
from pathlib import Path

try:
    from backend.ai_bridge import optimize_error
except Exception:
    def optimize_error(
        error_text: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        return {"status": "error", "msg": "ai_bridge not available"}

router = APIRouter()


@router.post("/ai/optimize")
def ai_optimize(payload: Dict[str, Any]):
    error_text = payload.get("error_text") or payload.get("text") or ""
    context = payload.get("context") or {}
    if not error_text:
        return {"code": 1, "error": "error_text is required"}
    result = optimize_error(error_text, context)
    # 写入 WS 日志广播（结构化）
    try:
        from backend.core.logger import ws_logger, emit_ws
        ws_payload = {
            "type": "AI_OPTIMIZE",
            "error_text": error_text[:5000],
            "result": result,
        }
        ws_logger.info(
            "AI_OPTIMIZE %s",
            json.dumps(ws_payload, ensure_ascii=False),
        )
        # 广播到当前所有 /ws/logs 订阅者
        import asyncio
        asyncio.create_task(
            emit_ws(json.dumps(ws_payload, ensure_ascii=False))
        )
    except Exception:
        # 广播失败不影响主流程
        pass
    return {"code": 0, "data": result}


@router.post("/ai/optimize/apply")
def ai_optimize_apply(payload: Dict[str, Any]):
    """接受前端的一条修复建议，生成最小补丁预览并通过 WS 广播。

    请求格式建议：
    {
      "fix": {"title": "...", "files": ["path"], "steps": ["..."], "patch": {"file":"path","diff":"..."}},
      "context": {"source": "monitor.html"}
    }
    返回：
    {"preview": {"files": [...], "patch": {...}}, "accepted": true}
    """
    fix = payload.get("fix") or {}
    context = payload.get("context") or {}
    files = fix.get("files") or []
    patch = fix.get("patch") or {}
    preview = {"files": files, "patch": patch, "title": fix.get("title")}
    resp = {"accepted": True, "preview": preview}

    # 广播到 WS
    try:
        from backend.core.logger import ws_logger, emit_ws
        ws_payload = {
            "type": "AI_APPLY_PREVIEW",
            "context": context,
            "preview": resp["preview"],
        }
        ws_logger.info(
            "AI_APPLY_PREVIEW %s",
            json.dumps(ws_payload, ensure_ascii=False),
        )
        import asyncio
        asyncio.create_task(
            emit_ws(json.dumps(ws_payload, ensure_ascii=False))
        )
    except Exception:
        pass
    return {"code": 0, "data": resp}


# === 受控补丁预演与应用 ===
_WHITELIST_DIRS = [
    Path("backend/api"),
    Path("frontend/pages"),
]

def _is_in_whitelist(file_path: str) -> bool:
    try:
        p = Path(file_path).resolve()
        root = Path(__file__).resolve().parents[2]
        rel = p.relative_to(root)
        return any(str(rel).startswith(str(d)) for d in _WHITELIST_DIRS)
    except Exception:
        return False


@router.post("/ai/optimize/patch-preview")
def ai_optimize_patch_preview(payload: Dict[str, Any]):
    patch = payload.get("patch") or {}
    file_path = patch.get("file")
    diff = patch.get("diff") or ""
    if not file_path or not diff:
        return {"code": 1, "error": "patch.file and patch.diff required"}
    allowed = _is_in_whitelist(file_path)
    resp = {
        "allowed": allowed,
        "file": file_path,
        "diff_len": len(diff),
    }
    try:
        from backend.core.logger import ws_logger, emit_ws
        ws_payload = {"type": "AI_PATCH_PREVIEW", "preview": resp}
        ws_logger.info("AI_PATCH_PREVIEW %s", json.dumps(ws_payload, ensure_ascii=False))
        import asyncio
        asyncio.create_task(emit_ws(json.dumps(ws_payload, ensure_ascii=False)))
    except Exception:
        pass
    return {"code": 0, "data": resp}


@router.post("/ai/optimize/patch-apply")
def ai_optimize_patch_apply(payload: Dict[str, Any]):
    """谨慎应用补丁：只允许白名单内的文件；目前直接覆盖写入文本，真实 diff 合并留作后续扩展。
    请求：{ patch: { file, content }, confirm: true }
    """
    patch = payload.get("patch") or {}
    file_path = patch.get("file")
    content = patch.get("content")
    confirm = bool(payload.get("confirm"))
    if not file_path or content is None:
        return {"code": 1, "error": "patch.file and patch.content required"}
    if not _is_in_whitelist(file_path):
        return {"code": 1, "error": "file not in whitelist"}
    if not confirm:
        return {"code": 1, "error": "confirm required"}
    try:
        p = Path(file_path).resolve()
        p.parent.mkdir(parents=True, exist_ok=True)
        # 直接覆盖写入（最小实现）；后续可改为真正的 diff 应用
        with open(p, "w", encoding="utf-8") as f:
            f.write(content)
        resp = {"applied": True, "file": str(p)}
        # 广播结果
        from backend.core.logger import ws_logger, emit_ws
        ws_payload = {"type": "AI_PATCH_APPLY", "result": resp}
        ws_logger.info("AI_PATCH_APPLY %s", json.dumps(ws_payload, ensure_ascii=False))
        import asyncio
        asyncio.create_task(emit_ws(json.dumps(ws_payload, ensure_ascii=False)))
        return {"code": 0, "data": resp}
    except Exception as e:
        return {"code": 1, "error": str(e)}


@router.post("/ai/optimize/patch-merge")
def ai_optimize_patch_merge(payload: Dict[str, Any]):
    """将统一 diff（V4A风格）解析为新的文件内容（最小实现）。
    请求：{ patch: { file, diff } }
    返回：{ file, content_len, content }
    规则：
    - 仅支持包含单个 "*** Update File: path" 区块的全量替换；
    - 对于以'+'开始的行，去掉'+'作为新内容；
    - 忽略以'-'开始的旧内容行；
    - 其他行（标记/上下文）忽略；
    - 若无法解析，则返回错误提示让前端传原始 content。
    """
    patch = payload.get("patch") or {}
    file_path = patch.get("file")
    diff = patch.get("diff") or ""
    if not file_path or not diff:
        return {"code": 1, "error": "patch.file and patch.diff required"}
    if not _is_in_whitelist(file_path):
        return {"code": 1, "error": "file not in whitelist"}
    lines = diff.splitlines()
    collecting = False
    new_lines = []
    try:
        for ln in lines:
            if ln.strip().startswith("*** Update File:"):
                collecting = True
                continue
            if ln.strip().startswith("*** End Patch"):
                break
            if not collecting:
                continue
            # 简单规则：仅采集以'+'开头的新内容行
            if ln.startswith('+'):
                new_lines.append(ln[1:])
            # 跳过'-'旧行和其他标记/上下文
        if not new_lines:
            return {"code": 1, "error": "unable to parse diff; provide patch.content"}
        content = "\n".join(new_lines)
        resp = {"file": file_path, "content_len": len(content), "content": content}
        # 广播合并预览
        from backend.core.logger import ws_logger, emit_ws
        ws_payload = {"type": "AI_PATCH_MERGE", "preview": {"file": file_path, "content_len": len(content)}}
        ws_logger.info("AI_PATCH_MERGE %s", json.dumps(ws_payload, ensure_ascii=False))
        import asyncio
        asyncio.create_task(emit_ws(json.dumps(ws_payload, ensure_ascii=False)))
        return {"code": 0, "data": resp}
    except Exception as e:
        return {"code": 1, "error": str(e)}


# === 增强：补丁解析、校验与测试 ===

def _run_cmd(cmd: List[str]) -> Dict[str, Any]:
    try:
        import subprocess
        p = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(Path(__file__).resolve().parents[2]),
        )
        return {"code": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as e:
        return {"code": -1, "stdout": "", "stderr": str(e)}


@router.post("/ai/optimize/patch-parse")
def ai_optimize_patch_parse(payload: Dict[str, Any]):
    """解析 V4A 风格补丁为结构化文件与块列表。"""
    patch_text = (payload.get("patch") or "").strip()
    if not patch_text:
        return {"code": 1, "error": "missing patch"}

    files: List[Dict[str, Any]] = []
    current: Dict[str, Any] = {}
    for ln in patch_text.splitlines():
        if ln.startswith("*** Update File:") or ln.startswith("*** Add File:") or ln.startswith("*** Delete File:"):
            if current:
                files.append(current)
            action = "Update" if "Update" in ln else ("Add" if "Add" in ln else "Delete")
            path = ln.split(":", 1)[1].strip()
            current = {"path": path, "action": action, "blocks": []}
        elif ln.startswith("@@"):
            current.setdefault("blocks", []).append({"marker": ln, "diff": []})
        elif ln.startswith("+") or ln.startswith("-") or ln.strip() == "":
            if current.get("blocks"):
                current["blocks"][-1]["diff"].append(ln)
    if current:
        files.append(current)

    # 白名单检查
    for f in files:
        if not _is_in_whitelist(f.get("path", "")):
            return {"code": 1, "error": f"path not allowed: {f.get('path')}"}

    from backend.core.logger import ws_logger, emit_ws
    ws_payload = {"type": "AI_PATCH_PARSE", "count": len(files)}
    ws_logger.info("AI_PATCH_PARSE %s", json.dumps(ws_payload, ensure_ascii=False))
    import asyncio
    asyncio.create_task(emit_ws(json.dumps(ws_payload, ensure_ascii=False)))
    return {"code": 0, "data": {"files": files}}


@router.post("/ai/optimize/patch-validate")
def ai_optimize_patch_validate(payload: Dict[str, Any]):
    """对目标文件执行 ruff 与 flake8 校验。"""
    files = [f for f in (payload.get("files") or []) if _is_in_whitelist(f)]
    if not files:
        return {"code": 1, "error": "no valid files"}
    ruff = _run_cmd(["python", "-m", "ruff", *files])
    flake = _run_cmd(["python", "-m", "flake8", *files])
    ok = ruff.get("code") == 0 and flake.get("code") == 0
    from backend.core.logger import ws_logger, emit_ws
    ws_payload = {"type": "AI_PATCH_VALIDATE", "ok": ok}
    ws_logger.info("AI_PATCH_VALIDATE %s", json.dumps(ws_payload, ensure_ascii=False))
    import asyncio
    asyncio.create_task(emit_ws(json.dumps(ws_payload, ensure_ascii=False)))
    return {"code": 0, "data": {"ok": ok, "ruff": ruff, "flake8": flake}}


@router.post("/ai/optimize/patch-test")
def ai_optimize_patch_test(payload: Dict[str, Any]):
    """运行快速冒烟测试（import app），可选执行 pytest。"""
    quick = bool(payload.get("quick", True))
    smoke = _run_cmd(["python", "-c", "import app; print('OK')"])
    pytest_res: Dict[str, Any] = {"skipped": True}
    if not quick:
        pytest_res = _run_cmd(["python", "-m", "pytest", "-q"])
    ok = smoke.get("code") == 0 and (pytest_res == {"skipped": True} or pytest_res.get("code") == 0)
    from backend.core.logger import ws_logger, emit_ws
    ws_payload = {"type": "AI_PATCH_TEST", "ok": ok}
    ws_logger.info("AI_PATCH_TEST %s", json.dumps(ws_payload, ensure_ascii=False))
    import asyncio
    asyncio.create_task(emit_ws(json.dumps(ws_payload, ensure_ascii=False)))
    return {"code": 0, "data": {"ok": ok, "smoke": smoke, "pytest": pytest_res}}
