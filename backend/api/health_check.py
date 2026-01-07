from fastapi import APIRouter, Request
from backend.core.response import SuccessResponse, ErrorResponse, ErrorCode
import time

router = APIRouter()

@router.get("/api/health/check")
async def health_check(request: Request):
    """
    系统健康状态检测 (统一响应格式 v1.1)
    
    返回系统运行状态、服务可用性、性能指标等
    """
    try:
        start_time = time.time()
        
        # 获取内核实例
        kernel = getattr(request.app.state, "kernel", None)
        kernel_status = "healthy" if kernel else "unavailable"
        
        # 基础健康检查
        health_data = {
            "status": kernel_status,
            "timestamp": time.time(),
            "response_time_ms": round((time.time() - start_time) * 1000, 2),
            "services": {
                "kernel": kernel_status,
                "api": "healthy",
            }
        }
        
        return SuccessResponse(
            data=health_data,
            message="System is healthy"
        )
    except Exception as e:
        return ErrorResponse(
            code=ErrorCode.INTERNAL_ERROR,
            message=f"Health check failed: {str(e)}"
        )
