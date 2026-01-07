from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/api/proxy/next")
async def get_next_proxy(request: Request):
    """
    获取下一个可用代理
    """
    # TODO: 实现代理池获取逻辑
    return {"status": "pending", "msg": "代理池获取功能待实现"}
