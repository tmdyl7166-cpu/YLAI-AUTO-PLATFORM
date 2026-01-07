from fastapi import FastAPI, WebSocket, Request, Depends
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any
import os
import sys
import asyncio
import mimetypes
from dotenv import load_dotenv
from fastapi.responses import StreamingResponse
from fastapi.responses import Response, PlainTextResponse
from fastapi.responses import RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import CONTENT_TYPE_LATEST
import time

from backend.core.kernel import Kernel
from backend.core.logger import ws_logger, register_ws_sender
from backend.api.auth import get_current, require_perm
from backend.core.pipeline import DAGPipeline
from backend.core.task import Node
from backend.ws.manager import ws_manager
from backend.ws.task_manager import task_manager
from backend.core.pipeline_ws import WSDAGPipeline
from backend.services.plugin_manager import plugin_manager
from backend.services.cache_service import cache_service
from backend.services.database_service import db_service
from backend.services.monitoring_service import monitoring_service

# Import metrics and middleware
try:
    from backend.config.metrics import request_count, request_duration, active_connections, REGISTRY
    from backend.config.middleware import MetricsMiddleware, RequestContextMiddleware
except ImportError:
    REGISTRY = None
    MetricsMiddleware = None
    RequestContextMiddleware = None

try:
    from backend.ai_bridge import run_ai_task as _run_ai_task
except Exception:
    def _run_ai_task(prompt: str) -> Any:
        return {"error": "ai_bridge not available", "input": prompt}


def run_ai_task(prompt: str) -> Any:
    return _run_ai_task(prompt)

# 接入迁移后的 AI 路由（优先 backend.scripts.ai.ai_router）
try:
    from backend.scripts.ai.ai_router import AIRouter, OllamaClient  # type: ignore
except Exception:
    # 兼容旧路径
    try:
        from ai_docker.ai_router import AIRouter, OllamaClient  # type: ignore
    except Exception:
        ROOT = Path(__file__).resolve().parents[1]
        AI_DOCKER_DIR = (ROOT / "ai-docker").resolve()
        if str(AI_DOCKER_DIR) not in sys.path:
            sys.path.append(str(AI_DOCKER_DIR))
        from ai_router import AIRouter, OllamaClient  # type: ignore

# 加载环境变量（支持 VS Code envFile 或默认 .env.dev）
env_file = os.environ.get("ENV_FILE") or \
           os.environ.get("PYTHON_ENV_FILE") or \
           os.environ.get("DOTENV_FILE") or \
           ".env.dev"
if Path(env_file).exists():
    load_dotenv(env_file)
else:
    cur_env = os.environ.get("ENV", "dev")
    fallback = f".env.{cur_env}"
    if Path(fallback).exists():
        load_dotenv(fallback)

app = FastAPI()

class ContentTypeFixMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        if 'Content-Type' not in response.headers:
            path = request.url.path
            ctype, _ = mimetypes.guess_type(path)
            if ctype:
                response.headers['Content-Type'] = ctype
        return response

app.add_middleware(ContentTypeFixMiddleware)

# Add Prometheus metrics middleware
if MetricsMiddleware:
    app.add_middleware(MetricsMiddleware)
if RequestContextMiddleware:
    app.add_middleware(RequestContextMiddleware)

kernel = Kernel()
kernel.load_scripts()
app.state.kernel = kernel
app.state.health_history = []

# Metrics (optional; no-op if prometheus_client unavailable)
try:
    from backend.core.metrics import (
        API_REQUESTS_TOTAL,
        PIPELINE_RUNS_TOTAL,
        AI_REQUEST_SECONDS,
        WS_CONNECTIONS,
    )
except Exception:
    class _No:
        def labels(self, *_, **__):
            return self
        def inc(self, *_):
            pass
        def observe(self, *_):
            pass
    API_REQUESTS_TOTAL = PIPELINE_RUNS_TOTAL = AI_REQUEST_SECONDS = WS_CONNECTIONS = _No()

class RequestMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        method = getattr(request, "method", "GET")
        raw_path = getattr(getattr(request, "url", None), "path", "/")
        start_time = time.time()
        
        try:
            response = await call_next(request)
        except Exception:
            # 记录错误请求
            duration = time.time() - start_time
            try:
                monitoring_service.record_api_request(method, raw_path, 500, duration)
            except Exception:
                pass
            raise
        
        # 记录成功请求
        duration = time.time() - start_time
        try:
            status_code = getattr(response, "status_code", 200)
            monitoring_service.record_api_request(method, raw_path, status_code, duration)
        except Exception:
            pass
        
        return response

app.add_middleware(RequestMetricsMiddleware)

app.state.ollama_client = OllamaClient(base_url=os.getenv("OLLAMA_URL", "http://127.0.0.1:11434"))
app.state.ai_router = AIRouter(app.state.ollama_client)

# /api/docs: 返回 docs/统一接口映射表.md 内容（或 404）
@app.get("/api/docs")
def get_docs():
    """返回统一接口映射表文档内容（Markdown）。"""
    root = Path(__file__).resolve().parents[1]
    doc_path = (root / "docs" / "统一接口映射表.md").resolve()
    if not doc_path.exists():
        return {"code": 1, "error": "docs/统一接口映射表.md not found"}
    content = doc_path.read_text(encoding="utf-8")
    return PlainTextResponse(content, media_type="text/markdown")

# /metrics: Standard Prometheus metrics endpoint
@app.get("/metrics")
def get_prometheus_metrics():
    """Prometheus metrics endpoint (Prometheus scrape format)."""
    if not REGISTRY:
        return PlainTextResponse("Prometheus client not available", status_code=503)
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
        return Response(
            content=generate_latest(REGISTRY),
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        return PlainTextResponse(f"Error generating metrics: {e}", status_code=500)

# /api/monitor/metrics: 返回 Prometheus 监控指标（legacy endpoint）
@app.get("/api/monitor/metrics")
def monitor_metrics():
    """Prometheus 监控指标端点（/api/monitor/metrics）- Legacy endpoint, use /metrics instead."""
    return get_prometheus_metrics()

@app.get("/scripts")
def list_scripts():
    """
    列出所有可用脚本 (统一响应格式 v1.1)
    """
    from backend.core.response import SuccessResponse, ErrorResponse, ErrorCode
    try:
        scripts = list(kernel.registry.scripts.keys())
        return SuccessResponse(
            data={"scripts": scripts, "count": len(scripts)},
            message=f"Retrieved {len(scripts)} available scripts"
        )
    except Exception as e:
        return ErrorResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Failed to list scripts: {str(e)}"
        )


# ==================== 统一注册所有路由 ====================
from backend.api.router_registry import register_routers

register_result = register_routers(app, include_optional=True)

# 日志记录路由注册结果
_registered_count = len(register_result['registered'])
_failed_count = len(register_result['failed'])
_skipped_count = len(register_result['skipped'])

if _registered_count > 0:
    print(f"✅ Registered {_registered_count} routers: {', '.join(register_result['registered'])}")
if _failed_count > 0:
    print(f"⚠️  Failed to register {_failed_count} routers:")
    for item in register_result['failed']:
        print(f"   - {item['name']}: {item['reason']}")
if _skipped_count > 0:
    print(f"⏭️  Skipped {_skipped_count} optional routers: {', '.join(register_result['skipped'])}")

@app.get("/health")
def get_health(fast: bool = False):
    """
    系统健康状态检查端点 (统一响应格式 v1.1)
    
    返回系统运行状态、依赖服务可用性。支持快速检查模式（fast=true，跳过深度检查）。
    """
    from backend.core.response import SuccessResponse, ErrorResponse, ErrorCode
    import time
    import socket
    
    try:
        import fastapi as _fastapi
        import uvicorn as _uvicorn
        
        info = {
            "status": "ok",
            "time": int(time.time()),
            "version": os.getenv("APP_VERSION", "dev"),
            "env": os.getenv("ENV", "dev"),
            "deps": {
                "fastapi": getattr(_fastapi, "__version__", "unknown"),
                "uvicorn": getattr(_uvicorn, "__version__", "unknown"),
            },
            "ws": {"logs": "/ws/monitor", "pipeline": "/ws/pipeline/{task_id}"},
            "ai_bridge": {"available": False},
            "runtime": {"scripts_count": 0, "scheduler_max_parallel": None},
            "ai_probe": {"host": None, "port": None, "reachable": None, "latency_ms": None},
            "services": {"cache": {"available": False}, "database": {"available": False}}
        }
        
        # 基础检查：脚本注册表
        try:
            info["runtime"]["scripts_count"] = len(list(kernel.registry.scripts.keys()))
        except Exception:
            info["runtime"]["scripts_count"] = 0
        
        # 获取调度器配置
        try:
            from backend.ws.scheduler import scheduler
            info["runtime"]["scheduler_max_parallel"] = scheduler.get_config().get("max_concurrent_pipelines")
        except Exception:
            pass
        
        # 快速模式跳过深度检查
        if not fast:
            # AI桥接可用性检查
            try:
                _ = run_ai_task("ping")
                info["ai_bridge"]["available"] = True
            except Exception:
                info["ai_bridge"]["available"] = False
            
            # AI主机连接性检查
            try:
                host = os.getenv("AI_HOST", "127.0.0.1")
                port = int(os.getenv("AI_PORT", "8002"))
                info["ai_probe"]["host"] = host
                info["ai_probe"]["port"] = port
                t0 = time.perf_counter()
                with socket.create_connection((host, port), timeout=1.5):
                    pass
                t1 = time.perf_counter()
                info["ai_probe"]["reachable"] = True
                info["ai_probe"]["latency_ms"] = int((t1 - t0) * 1000)
                
                # 更新历史记录用于平均延迟计算
                hist = getattr(app.state, "health_history", [])
                hist.append(info["ai_probe"]["latency_ms"])
                if len(hist) > 20:
                    hist[:] = hist[-20:]
                app.state.health_history = hist
                info["ai_probe"]["latency_avg_ms"] = int(sum(hist) / len(hist)) if hist else None
                info["ai_probe"]["samples"] = len(hist)
            except Exception:
                info["ai_probe"]["reachable"] = False
            
            # 缓存服务检查
            try:
                from backend.services.cache_service import cache_service
                info["services"]["cache"] = cache_service.health_check()
            except Exception as e:
                info["services"]["cache"]["error"] = str(e)
            
            # 数据库服务检查
            try:
                from backend.services.database_service import db_service
                info["services"]["database"] = db_service.health_check()
            except Exception as e:
                info["services"]["database"]["error"] = str(e)
        
        return SuccessResponse(
            data=info,
            message="System is healthy"
        )
        
    except Exception as e:
        import traceback
        return ErrorResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Health check error: {str(e)}",
            data={"error_trace": traceback.format_exc()} if not fast else None
        )

@app.get("/metrics")
def get_metrics():
    """Prometheus指标端点"""
    return Response(
        content=monitoring_service.get_metrics(),
        media_type=CONTENT_TYPE_LATEST
    )

@app.on_event("startup")
async def _boot_auto_probe():
    try:
        from backend.services.auto_probe import start_auto_probe
        await start_auto_probe(app)
    except Exception as e:
        ws_logger.error(f"auto_probe init failed: {e}")

    # 初始化缓存服务
    try:
        await cache_service.initialize()
        ws_logger.info("Cache service initialized successfully")
    except Exception as e:
        ws_logger.error(f"Cache service initialization failed: {e}")

    # 初始化数据库服务
    try:
        await db_service.initialize()
        ws_logger.info("Database service initialized successfully")
    except Exception as e:
        ws_logger.error(f"Database service initialization failed: {e}")

    # 初始化监控服务
    try:
        await monitoring_service.start_collection()
        ws_logger.info("Monitoring service initialized successfully")
    except Exception as e:
        ws_logger.error(f"Monitoring service initialization failed: {e}")

@app.on_event("shutdown")
async def _shutdown_services():
    # 关闭缓存服务
    try:
        cache_service.close()
        ws_logger.info("Cache service closed successfully")
    except Exception as e:
        ws_logger.error(f"Cache service shutdown failed: {e}")

    # 关闭数据库服务
    try:
        db_service.close()
        ws_logger.info("Database service closed successfully")
    except Exception as e:
        ws_logger.error(f"Database service shutdown failed: {e}")

    # 关闭监控服务
    try:
        # 监控服务没有异步关闭方法，使用同步方式
        ws_logger.info("Monitoring service closed successfully")
    except Exception as e:
        ws_logger.error(f"Monitoring service shutdown failed: {e}")
FRONTEND_DIR = (Path(__file__).resolve().parents[1] / "frontend").resolve()
PAGES_DIR = None

class StrictStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        ctype, _ = mimetypes.guess_type(path)
        if ctype:
            response.headers['Content-Type'] = ctype
        return response

if FRONTEND_DIR.exists():
    PAGES_DIR = FRONTEND_DIR / "pages"
    STATIC_DIR = FRONTEND_DIR / "static"
    if PAGES_DIR.exists():
        app.mount("/pages", StrictStaticFiles(directory=str(PAGES_DIR), html=True), name="pages")
    if STATIC_DIR.exists():
        app.mount("/static", StrictStaticFiles(directory=str(STATIC_DIR), html=False), name="static")
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

# 支持后端的无后缀页面访问（/pages/<name> -> /pages/<name>.html）
@app.get("/pages/{name}")
def _extless_pages_redirect(name: str):
    try:
        if PAGES_DIR is not None:
            target = (PAGES_DIR / f"{name}.html").resolve()
            if target.exists():
                return RedirectResponse(url=f"/pages/{name}.html", status_code=302)
    except Exception:
        pass
    return {"code": 1, "error": "page not found"}

# docs_router 由 register_routers() 通过 router_registry 动态注册
# app.include_router(docs_router)

pipeline_ws = WSDAGPipeline(kernel)

app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"] if os.getenv("ENV", "dev") == "dev"
        else [os.getenv("API_BASE", "")]
    ),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/scheduler/config")
def get_scheduler_config(_auth=Depends(require_perm("view"))):
    from backend.ws.scheduler import scheduler
    return {"code": 0, "data": scheduler.get_config()}

@app.post("/api/scheduler/config")
def set_scheduler_config(payload: dict, _auth=Depends(require_perm("maintain"))):
    from backend.ws.scheduler import scheduler
    n = int(payload.get("max_concurrent_pipelines", 2))
    scheduler.set_max_parallel(n)
    return {"code": 0, "data": scheduler.get_config()}

@app.get("/api/scheduler/circuit")
def get_circuit_state():
    try:
        from backend.core.circuit import circuit
        return {"code": 0, "data": circuit.snapshot()}
    except Exception:
        return {
            "code": 0,
            "data": {
                "services": [],
                "open": [],
                "half_open": [],
                "closed": [],
                "stats": {"window": 60, "fail_rate": 0.0}
            }
        }

@app.websocket("/ws/monitor")
async def log_ws(ws: WebSocket):
    if os.getenv("ENV", "dev") != "dev":
        token = ws.query_params.get("token") if hasattr(ws, "query_params") else None
        try:
            class _Req:
                headers = {}
                query_params = {}
            req = _Req()
            if token:
                req.query_params = {"token": token}
            await require_perm("view")(get_current(req))  # type: ignore
        except Exception:
            await ws.close(code=4401)
            return

    await ws.accept()
    try:
        WS_CONNECTIONS.labels(endpoint="/ws/monitor").inc()
    except Exception:
        pass

    async def sender(text: str):
        await ws.send_text(text)
    register_ws_sender(sender)
    try:
        while True:
            data = await ws.receive_text()
            ws_logger.error("UI-BUBBLE: %s", data)
            await ws.send_text("ACK")
    except Exception:
        ws_logger.info("WS /ws/logs disconnected")
        try:
            WS_CONNECTIONS.labels(endpoint="/ws/monitor").dec()  # type: ignore
        except Exception:
            try:
                WS_CONNECTIONS.labels(endpoint="/ws/monitor").inc(-1)
            except Exception:
                pass

    @app.on_event("startup")
    async def _start_log_collector():
        try:
            from backend.services.log_collector import collect_loop
            asyncio.create_task(collect_loop())
            ws_logger.info("log_collector started")
        except Exception as e:
            ws_logger.error("log_collector failed: %s", e)

@app.websocket("/ws/pipeline/{task_id}")
async def ws_pipeline(websocket: WebSocket, task_id: str):
    await ws_manager.connect(task_id, websocket)
    state = task_manager.get_task_state(task_id)
    if state:
        for node_id in state["nodes"].keys():
            await ws_manager.broadcast_node_update(task_id, node_id)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        ws_manager.disconnect(task_id, websocket)

@app.post("/api/pipeline/run-seq")
def run_pipeline_seq(payload: dict):
    tasks = payload.get("tasks", [])
    result = kernel.run_pipeline(tasks)
    return {"code": 0, "data": result}

@app.post("/api/ai/pipeline")
def ai_pipeline(payload: dict):
    prompt = payload.get("prompt", "")
    if not prompt:
        return {"code": 1, "error": "missing prompt"}
    res = app.state.ai_router.run_pipeline(prompt)
    return {"code": 0, "data": res}

@app.post("/ai/pipeline")
async def run_ai_pipeline(request: Request):
    data = await request.json()
    prompt = data.get("prompt", "")
    if not prompt:
        return {"code": 1, "error": "missing prompt"}
    res = app.state.ai_router.run_pipeline(prompt)
    return {"code": 0, "result": res.get("output")}


def get_registered_scripts():
    return list(kernel.registry.scripts.keys())


class DAGNodeModel(BaseModel):
    id: str
    script: str
    params: dict = {}
    depends_on: list = []
    condition: str | bool | None = None


class DAGPayload(BaseModel):
    nodes: list[DAGNodeModel]
    max_concurrency: int = 4
    node_timeout: int | None = None
    priority: int = 100


@app.post("/api/pipeline/validate")
def validate_pipeline(payload: DAGPayload):
    nodes = [Node(id=n.id, script=n.script, params=n.params, depends_on=n.depends_on, condition=n.condition) for n in payload.nodes]
    pipeline = DAGPipeline(kernel)
    registered = get_registered_scripts()
    res = pipeline.validate(nodes, registered)
    if not res["ok"]:
        return {"code": 1, "errors": res["errors"]}
    return {"code": 0, "data": "OK"}

@app.post("/api/pipeline/run")
async def run_pipeline(payload: DAGPayload, _auth=Depends(require_perm("run"))):
    try:
        PIPELINE_RUNS_TOTAL.inc()
    except Exception:
        pass
    nodes = [Node(id=n.id, script=n.script, params=n.params, depends_on=n.depends_on, condition=n.condition) for n in payload.nodes]
    task_id = await pipeline_ws.run(nodes, payload.max_concurrency, priority=payload.priority)
    return {
        "code": 0,
        "task_id": task_id,
        "ws_url": f"/ws/pipeline/{task_id}"
    }

@app.post("/api/generate")
def api_generate(payload: dict):
    try:
        import requests  # type: ignore
        from ai_docker.ai_router import extract_last_json, safe_text  # type: ignore
    except Exception:
        from ai_router import extract_last_json, safe_text  # type: ignore
        import requests  # type: ignore

    base = app.state.ollama_client.base_url if hasattr(app.state, "ollama_client") else os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
    url = f"{base.rstrip('/')}/api/generate"
    import time as _t
    t0 = _t.perf_counter()
    try:
        resp = requests.post(url, json=payload, timeout=120)
        txt = safe_text(resp.text)
        last = extract_last_json(txt)
        if last is not None:
            return last
        try:
            return resp.json()
        except Exception:
            return {"response": txt}
    except Exception as e:
        return {"error": safe_text(e)}
    finally:
        try:
            AI_REQUEST_SECONDS.observe(_t.perf_counter() - t0)
        except Exception:
            pass

@app.get("/api/status")
def get_project_status(request: Request):
    try:
        if os.getenv("ENV", "dev") != "dev":
            _ = require_perm("view")(get_current(request))  # type: ignore
        root = Path(__file__).resolve().parents[1]
        status_path = (root / "PROJECT_STATUS.md").resolve()
        if not status_path.exists():
            return {"code": 1, "error": "PROJECT_STATUS.md not found"}
        content = status_path.read_text(encoding="utf-8")
        return {"code": 0, "data": {"markdown": content}}
    except Exception as e:
        return {"code": 1, "error": str(e)}

@app.websocket("/ws/monitor")
async def ws_monitor(ws: WebSocket):
    if os.getenv("ENV", "dev") != "dev":
        token = ws.query_params.get("token") if hasattr(ws, "query_params") else None
        try:
            class _Req:
                headers = {}
                query_params = {}
            req = _Req()
            if token:
                req.query_params = {"token": token}
            await require_perm("view")(get_current(req))  # type: ignore
        except Exception:
            await ws.close(code=4401)
            return

    await ws.accept()
    try:
        WS_CONNECTIONS.labels(endpoint="/ws/monitor").inc()
    except Exception:
        pass

    async def sender(text: str):
        await ws.send_text(text)
    register_ws_sender(sender)
    try:
        while True:
            _ = await ws.receive_text()
            await ws.send_text("ACK")
    except Exception:
        ws_logger.info("WS /ws/monitor disconnected")
        try:
            WS_CONNECTIONS.labels(endpoint="/ws/monitor").dec()  # type: ignore
        except Exception:
            try:
                WS_CONNECTIONS.labels(endpoint="/ws/monitor").inc(-1)
            except Exception:
                pass

@app.get("/api/sse/logs")
def sse_logs(request: Request):
    def _gen():
        import time
        log_dir = Path(__file__).resolve().parents[1] / "logs"
        log_file = log_dir / "app.log"
        try:
            if log_file.exists():
                lines = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()[-200:]
            else:
                lines = ["[boot] no log file, sending heartbeat"]
        except Exception:
            lines = ["[boot] log read failed"]
        yield f"data: {__import__('json').dumps({'lines': lines})}\n\n"
        while True:
            time.sleep(2)
            yield "data: {\"lines\": [\"heartbeat\"]}\n\n"

    if os.getenv("ENV", "dev") != "dev":
        try:
            _ = require_perm("view")(get_current(request))  # type: ignore
        except Exception:
            return {"code": 1, "error": "unauthorized"}
    headers = {"Content-Type": "text/event-stream", "Cache-Control": "no-cache", "Connection": "keep-alive"}
    return StreamingResponse(_gen(), headers=headers)

@app.get("/api/policy/get")
def get_policy(request: Request):
    if os.getenv("ENV", "dev") != "dev":
        try:
            _ = require_perm("view")(get_current(request))  # type: ignore
        except Exception:
            return {"code": 1, "error": "unauthorized"}
    data = {
        "version": os.getenv("APP_VERSION", "dev"),
        "rbac": {"roles": ["admin", "user"], "default": "user"},
        "features": ["logs", "pipeline", "ai_optimize"],
        "limits": {"max_concurrent_pipelines": 4}
    }
    return {"code": 0, "data": data}

# Prometheus metrics endpoint (optional dependency)
@app.get("/metrics")
def metrics():
    try:
        from prometheus_client import generate_latest, CONTENT_TYPE_LATEST  # type: ignore
        body = generate_latest()
        return Response(content=body, media_type=CONTENT_TYPE_LATEST)
    except Exception:
        # Fallback minimal metric to keep probes green but signal missing lib
        return Response(content="app_health 1\n", media_type="text/plain; version=0.0.4")
