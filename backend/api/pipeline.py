import asyncio
import json
import time
from typing import Dict
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from backend.core.kernel import run_pipeline
from backend.api.auth import require_perm
from backend.services.database_service import db_service
from backend.services.monitoring_service import monitoring_service
from backend.core.logger import api_logger


router = APIRouter(prefix="/api/pipeline/simple")

# 内存保存任务
tasks: Dict[str, list] = {}


@router.post("/run")
async def run_pipeline_api(payload: dict, user=Depends(require_perm("run"))):
    start_time = time.time()
    nodes = payload.get("nodes", [])
    task_id = str(len(tasks) + 1)
    tasks[task_id] = nodes

    try:
        # 记录流水线运行到数据库
        await db_service.log_pipeline_run(
            task_id=task_id,
            user_id=user.get('id'),
            nodes_count=len(nodes),
            status="started"
        )
        api_logger.info(f"Pipeline run logged: task_id={task_id}, user={user.get('username')}, nodes={len(nodes)}")

        # 记录监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/pipeline/simple/run", 200, duration)
        monitoring_service.record_pipeline_run("started")

        return {"task_id": task_id}
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/pipeline/simple/run", 500, duration)
        monitoring_service.record_pipeline_run("error")
        raise


@router.websocket("/ws/{task_id}")
async def pipeline_ws(websocket: WebSocket, task_id: str):
    await websocket.accept()
    nodes = tasks.get(task_id, [])

    # 记录WebSocket连接监控指标
    monitoring_service.record_websocket_connection("pipeline", "connected")

    # 使用线程安全推送（事件循环中转）
    def ws_send(node_id, msg):
        payload = json.dumps({"task_id": task_id, "node_id": node_id, **msg}, ensure_ascii=False)
        loop = asyncio.get_event_loop()
        loop.call_soon_threadsafe(asyncio.create_task, websocket.send_text(payload))

    try:
        # 在线程中运行简易 DAG，避免阻塞事件循环
        await asyncio.to_thread(run_pipeline, nodes, 4, ws_send)
        await websocket.send_text(json.dumps({"task_id": task_id, "node_id": "__pipeline__", "type": "pipeline_end"}))

        # 更新流水线状态为完成
        try:
            await db_service.update_pipeline_status(task_id, "completed")
            api_logger.info(f"Pipeline completed: task_id={task_id}")
            monitoring_service.record_pipeline_run("completed")
        except Exception as e:
            api_logger.error(f"Failed to update pipeline status: {e}")

    except WebSocketDisconnect:
        # 客户端断开，更新状态为中断
        try:
            await db_service.update_pipeline_status(task_id, "interrupted")
            api_logger.warning(f"Pipeline interrupted: task_id={task_id}")
            monitoring_service.record_pipeline_run("interrupted")
        except Exception as e:
            api_logger.error(f"Failed to update pipeline status on disconnect: {e}")
        pass
    finally:
        # 记录WebSocket断开监控指标
        monitoring_service.record_websocket_connection("pipeline", "disconnected")