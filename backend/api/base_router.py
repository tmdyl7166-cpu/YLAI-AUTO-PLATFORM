from typing import Dict, Any
from fastapi import APIRouter, Request, Depends, Body
from fastapi.responses import StreamingResponse
import asyncio
import os
import json
import time
from backend.core.logger import api_logger
from backend.api.auth import require_perm
from backend.core.response import SuccessResponse, ErrorResponse, ErrorCode, PaginatedResponse
from backend.services.snapshot import store as snapshot_store
from backend.ai_bridge import run_ai_task
from backend.core.logger import LOG_DIR
from backend.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/api")


@router.get("/modules")
async def get_modules(request: Request, _auth=Depends(require_perm("view"))):
    """获取所有可用模块 (统一响应格式 v1.1)"""
    start_time = time.time()
    try:
        kernel = getattr(request.app.state, "kernel", None)
        if not kernel:
            duration = time.time() - start_time
            monitoring_service.record_api_request("GET", "/api/modules", 500, duration)
            return ErrorResponse(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message="Kernel not initialized"
            )
        data = list(kernel.registry.scripts.keys())
        api_logger.info("GET /api/modules -> %d modules", len(data))
        
        return SuccessResponse(
            data={"modules": data, "count": len(data)},
            message=f"Retrieved {len(data)} modules"
        )
        result = {"code": 0, "data": data}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/modules", 200, duration)
        return result
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/modules", 500, duration)
        raise


# 兼容别名：/api/scripts 与 /api/modules 返回相同内容
@router.get("/scripts")
async def get_scripts_alias(request: Request, _auth=Depends(require_perm("view"))):
    start_time = time.time()
    try:
        kernel = getattr(request.app.state, "kernel", None)
        if not kernel:
            # 记录服务不可用监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("GET", "/api/scripts", 500, duration)
            return {"code": 1, "error": "kernel not initialized"}
        data = list(kernel.registry.scripts.keys())
        api_logger.info("GET /api/scripts -> %d scripts", len(data))
        result = {"code": 0, "data": data}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/scripts", 200, duration)
        return result
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/scripts", 500, duration)
        raise


@router.post("/run")
async def post_run(payload: Dict[str, Any], request: Request, _auth=Depends(require_perm("run"))):
    start_time = time.time()
    try:
        kernel = getattr(request.app.state, "kernel", None)
        if not kernel:
            # 记录服务不可用监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/run", 500, duration)
            return {"code": 1, "error": "kernel not initialized"}
        name = payload.get("script")
        params = payload.get("params", {})
        api_logger.info("POST /api/run script=%s params=%s", name, params)
        result = kernel.run(name, **params)
        response = {"code": 0, "data": result}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/run", 200, duration)
        monitoring_service.record_script_execution(name, "success")
        return response
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/run", 500, duration)
        name = payload.get("script", "unknown") if 'payload' in locals() else "unknown"
        monitoring_service.record_script_execution(name, "error")
        raise


# 简易任务启动端点（供监控页触发脚本）
@router.post("/crawler/start")
async def start_crawler(payload: Dict[str, Any], request: Request, _auth=Depends(require_perm("run"))):
    """
    兼容前端 monitor.js：
    POST /api/crawler/start { script, params?, interval?, path? }
    这里直接触发一次脚本运行；若需周期调度，请后续接入 scheduler。
    """
    start_time = time.time()
    try:
        kernel = getattr(request.app.state, "kernel", None)
        if not kernel:
            # 记录服务不可用监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/crawler/start", 500, duration)
            return {"code": 1, "error": "kernel not initialized"}
        name = payload.get("script")
        params = payload.get("params", {}) or {}
        if not name:
            # 记录无效请求监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/crawler/start", 400, duration)
            return {"code": 1, "error": "missing script"}

        async def _run_once():
            loop = asyncio.get_running_loop()
            try:
                await asyncio.to_thread(kernel.run, name, **params)
                api_logger.info("crawler.start finished: %s", name)
                monitoring_service.record_script_execution(name, "success")
            except Exception as e:
                api_logger.error("crawler.start error: %s", e)
                monitoring_service.record_script_execution(name, "error")

        asyncio.create_task(_run_once())
        api_logger.info("POST /api/crawler/start script=%s params=%s", name, params)
        result = {"code": 0, "message": "started", "script": name}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/crawler/start", 200, duration)
        return result
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/crawler/start", 500, duration)
        raise


@router.post("/ai")
async def post_ai(payload: Dict[str, Any], _auth=Depends(require_perm("run"))):
    start_time = time.time()
    try:
        prompt = payload.get("prompt")
        api_logger.info("POST /api/ai prompt_len=%s", len(prompt or ""))
        result = await run_ai_task(prompt)
        response = {"code": 0, "data": result}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/ai", 200, duration)
        monitoring_service.record_ai_task("success")
        return response
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/ai", 500, duration)
        monitoring_service.record_ai_task("error")
        raise

@router.post("/api/generate")
async def post_generate(payload: Dict[str, Any] = Body(...)):
    """代理到本地 Ollama 的 /api/generate，供前端演示页使用。"""
    start_time = time.time()
    try:
        try:
            import requests  # type: ignore
            from ai_docker.ai_router import extract_last_json, safe_text  # type: ignore
        except Exception:
            from ai_router import extract_last_json, safe_text  # type: ignore
            import requests  # type: ignore

        base = os.getenv("OLLAMA_URL_BASE", os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")).rstrip("/")
        url = f"{base}/api/generate"
        resp = requests.post(url, json=payload, timeout=120)
        txt = safe_text(resp.text)
        last = extract_last_json(txt)
        if last is not None:
            # 记录成功监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/generate", 200, duration)
            monitoring_service.record_ai_generation("success")
            return last
        try:
            result = resp.json()
            # 记录成功监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/generate", 200, duration)
            monitoring_service.record_ai_generation("success")
            return result
        except Exception:
            result = {"response": txt}
            # 记录成功监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/generate", 200, duration)
            monitoring_service.record_ai_generation("success")
            return result
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/generate", 500, duration)
        monitoring_service.record_ai_generation("error")
        return {"error": safe_text(e)}


@router.get("/status")
async def get_status(request: Request, _auth=Depends(require_perm("view"))):
    start_time = time.time()
    try:
        kernel = getattr(request.app.state, "kernel", None)
        if not kernel:
            # 记录服务不可用监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("GET", "/api/status", 500, duration)
            return {"code": 1, "error": "kernel not initialized"}
        data = {"scripts": list(kernel.registry.scripts.keys()), "status": "running"}
        api_logger.info("GET /api/status -> %s", data["status"])
        result = {"code": 0, "data": data}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/status", 200, duration)
        return result
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/status", 500, duration)
        raise


@router.post("/snapshot")
async def post_snapshot(payload: Dict[str, Any], request: Request):
    start_time = time.time()
    try:
        kind = payload.get("kind") or "generic"
        info = snapshot_store.save(kind, payload)
        api_logger.info("POST /api/snapshot kind=%s id=%s", kind, info.get("id"))
        result = {"code": 0, "data": info}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/snapshot", 200, duration)
        return result
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/snapshot", 500, duration)
        raise


@router.get("/snapshot/list")
async def list_snapshot(request: Request):
    start_time = time.time()
    try:
        items = snapshot_store.list()
        result = {"code": 0, "data": items}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/snapshot/list", 200, duration)
        return result
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/snapshot/list", 500, duration)
        raise


@router.get("/snapshot/{snap_id}")
async def get_snapshot(snap_id: str, request: Request):
    start_time = time.time()
    try:
        item = snapshot_store.get(snap_id)
        if not item:
            # 记录未找到监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("GET", f"/api/snapshot/{snap_id}", 404, duration)
            return {"code": 1, "error": "not found"}
        result = {"code": 0, "data": item}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", f"/api/snapshot/{snap_id}", 200, duration)
        return result
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", f"/api/snapshot/{snap_id}", 500, duration)
        raise


# SSE 日志流（兼容前端 monitor.js 的 EventSource('/api/sse/logs')）
@router.get("/sse/logs")
async def sse_logs(_auth=Depends(require_perm("view"))):
    start_time = time.time()
    try:
        log_file = os.path.join(str(LOG_DIR), "ws.log")

        async def event_gen():
            # 若日志文件不存在，先等待创建
            for _ in range(10):
                if os.path.exists(log_file):
                    break
                yield "data: {\"lines\":[\"waiting logs...\"]}\n\n"
                await asyncio.sleep(0.5)

            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    # 从文件末尾开始
                    f.seek(0, os.SEEK_END)
                    while True:
                        line = f.readline()
                        if not line:
                            await asyncio.sleep(0.8)
                            continue
                        data = line.rstrip("\n")
                        payload = json.dumps({"lines": [data]}, ensure_ascii=False)
                        yield f"data: {payload}\n\n"
            except asyncio.CancelledError:
                # 连接关闭
                return
            except Exception as e:
                # 输出错误消息并结束
                err = json.dumps({"lines": [f"sse error: {e}"]}, ensure_ascii=False)
                yield f"data: {err}\n\n"

        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
        # 记录SSE连接建立监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/sse/logs", 200, duration)
        monitoring_service.record_sse_connection("logs", "connected")
        return StreamingResponse(event_gen(), media_type="text/event-stream", headers=headers)
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/sse/logs", 500, duration)
        raise


@router.post("/demo/run")
async def post_demo_run(payload: Dict[str, Any], request: Request, _auth=Depends(require_perm("execute"))):
    """
    演示脚本运行接口

    请求体参数:
    - message: str, 可选，输入消息，默认为 'Hello, YeLing!'

    返回:
    - code: int, 状态码 (0=成功, 1=失败)
    - data: dict, 执行结果
    - error: str, 错误信息 (失败时)
    """
    start_time = time.time()
    try:
        message = payload.get("message", "Hello, YeLing!")

        api_logger.info("POST /demo/run message='%s'", message)

        # 调用演示脚本
        kernel = getattr(request.app.state, "kernel", None)
        if not kernel:
            # 记录服务不可用监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/demo/run", 500, duration)
            return {"code": 1, "error": "kernel not initialized"}

        # 异步执行脚本
        result = await asyncio.to_thread(kernel.run, "demo_run", message=message)

        api_logger.info("POST /demo/run completed: %s", result)

        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/demo/run", 200, duration)
        monitoring_service.record_script_execution("demo_run", "success")

        return {"code": 0, "data": result}

    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/demo/run", 500, duration)
        monitoring_service.record_script_execution("demo_run", "error")

        api_logger.error("POST /demo/run error: %s", e)
        return {"code": 1, "error": str(e)}
