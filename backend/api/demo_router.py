"""
Demo API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.core.registry import registry
from backend.api.auth import require_perm
from backend.core.logger import api_logger
import traceback

router = APIRouter()

@router.post("/api/demo/run")
async def run_demo(
    data: dict,
    user=Depends(require_perm("run"))
):
    """
    演示脚本运行接口

    请求体参数:
    - message: str, 可选，输入消息，默认为"Hello, YeLing!"

    返回:
    - echo: str, 原消息回显
    - length: int, 消息长度
    - upper: str, 大写转换
    - lower: str, 小写转换
    """
    try:
        message = data.get("message", "Hello, YeLing!").strip()

        if len(message) > 1000:
            api_logger.warning(f"Demo run: message too long ({len(message)} chars) from user {user.get('username')}")
            raise HTTPException(status_code=400, detail="Message too long (max 1000 characters)")

        api_logger.info(f"Demo run: processing message (length: {len(message)}) for user {user.get('username')}")

        # 调用注册的脚本
        script = registry.get("demo_run")
        if not script:
            api_logger.error("Demo run: script 'demo_run' not found in registry")
            raise HTTPException(status_code=500, detail="Demo service unavailable")

        result = await script.run(message=message)

        api_logger.info(f"Demo run: completed for user {user.get('username')}, result keys: {list(result.keys()) if isinstance(result, dict) else 'non-dict'}")
        return result

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"Demo run failed: {str(e)}"
        api_logger.error(f"{error_msg}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="Internal server error during demo execution")