from fastapi import APIRouter, Query
from backend.ws.task_manager import task_manager

router = APIRouter()


@router.get("/api/tasks")
def list_tasks(page: int = Query(1, ge=1), limit: int = Query(10, ge=1, le=100)):
    all_tasks = task_manager.list_tasks()
    start = (page - 1) * limit
    end = start + limit
    paginated = all_tasks[start:end]
    return {"code": 0, "data": paginated, "total": len(all_tasks), "page": page, "limit": limit}


@router.post("/api/tasks/{task_id}/priority")
def set_priority(task_id: str, payload: dict):
    try:
        prio = int(payload.get("priority", 100))
        st = task_manager.get_task_state(task_id)
        if not st:
            return {"code": 1, "error": "task not found"}
        task_manager.set_task_queue_status(task_id, st.get("queue_status", "queued"), priority=prio)
        return {"code": 0, "data": {"task_id": task_id, "priority": prio}}
    except Exception as e:
        return {"code": 1, "error": str(e)}