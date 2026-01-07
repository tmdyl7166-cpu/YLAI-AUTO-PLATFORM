from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/api/task/dispatch")
async def dispatch_task(request: Request):
    """
    分发采集任务到各节点
    """
    # TODO: 实现分布式任务调度逻辑
    return {"status": "pending", "msg": "分布式任务调度功能待实现"}
