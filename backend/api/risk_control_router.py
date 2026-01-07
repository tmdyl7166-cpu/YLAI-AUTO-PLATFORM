"""
风控识别与突破API路由
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging

from backend.services.risk_control import RiskDetector, CaptchaSolver, StrategyManager
from backend.api.auth import get_current, require_perm

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/risk-control", tags=["risk-control"])

# 全局服务实例
risk_detector = RiskDetector()
captcha_solver = CaptchaSolver()
strategy_manager = StrategyManager()

class DetectRiskRequest(BaseModel):
    html: str
    headers: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = 200

class CaptchaSolveRequest(BaseModel):
    image: str  # base64或URL
    engine: Optional[str] = "auto"

class StrategyExecuteRequest(BaseModel):
    action: str
    params: Optional[Dict[str, Any]] = None

@router.post("/detect-risk-type")
async def detect_risk_type(
    request: DetectRiskRequest,
    current_user: Dict = Depends(require_perm("risk_control:read"))
):
    """
    检测风控类型

    Args:
        request: 检测请求

    Returns:
        风控检测结果
    """
    try:
        risk_type, details = risk_detector.detect_risk_type(
            request.html,
            request.headers,
            request.status_code
        )

        return {
            "success": True,
            "risk_type": risk_type.value,
            "detected": risk_type.name != "NONE",
            "details": details,
            "timestamp": "2025-12-22T00:00:00Z"
        }

    except Exception as e:
        logger.error(f"风控检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")

@router.post("/run-captcha-solver")
async def run_captcha_solver(
    request: CaptchaSolveRequest,
    current_user: Dict = Depends(require_perm("risk_control:write"))
):
    """
    运行验证码解决器

    Args:
        request: 验证码解决请求

    Returns:
        解决结果
    """
    try:
        result = captcha_solver.run_captcha_solver(
            request.image,
            engine=request.engine
        )

        return {
            "success": result["success"],
            "result": result["result"],
            "engine": result["engine"],
            "time_taken": result["time_taken"],
            "available_engines": result["available_engines"],
            "timestamp": "2025-12-22T00:00:00Z"
        }

    except Exception as e:
        logger.error(f"验证码解决失败: {e}")
        raise HTTPException(status_code=500, detail=f"解决失败: {str(e)}")

@router.post("/execute-with-strategy")
async def execute_with_strategy(
    request: StrategyExecuteRequest,
    current_user: Dict = Depends(require_perm("risk_control:write"))
):
    """
    使用策略执行动作

    Args:
        request: 策略执行请求

    Returns:
        执行结果
    """
    try:
        # 这里可以根据action类型调用不同的处理函数
        # 暂时返回模拟结果
        def mock_action(**params):
            return {
                "status": "success",
                "data": params,
                "risk_detected": False,
                "risk_type": "none"
            }

        result = strategy_manager.execute_with_strategy(
            mock_action,
            **(request.params or {})
        )

        return {
            "success": True,
            "result": result,
            "strategy_used": strategy_manager.current_strategy.value,
            "timestamp": "2025-12-22T00:00:00Z"
        }

    except Exception as e:
        logger.error(f"策略执行失败: {e}")
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")

@router.get("/strategy-stats")
async def get_strategy_stats(
    current_user: Dict = Depends(require_perm("risk_control:read"))
):
    """
    获取策略统计信息

    Returns:
        策略统计数据
    """
    try:
        stats = strategy_manager.get_strategy_stats()
        return {
            "success": True,
            "stats": stats,
            "timestamp": "2025-12-22T00:00:00Z"
        }

    except Exception as e:
        logger.error(f"获取策略统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")

@router.post("/reset-strategy")
async def reset_strategy(
    current_user: Dict = Depends(require_perm("risk_control:admin"))
):
    """
    重置策略管理器

    Returns:
        重置结果
    """
    try:
        strategy_manager.reset()
        return {
            "success": True,
            "message": "策略管理器已重置",
            "timestamp": "2025-12-22T00:00:00Z"
        }

    except Exception as e:
        logger.error(f"重置策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"重置失败: {str(e)}")

@router.get("/available-engines")
async def get_available_engines(
    current_user: Dict = Depends(require_perm("risk_control:read"))
):
    """
    获取可用OCR引擎

    Returns:
        可用引擎列表
    """
    try:
        engines = captcha_solver.get_available_engines()
        return {
            "success": True,
            "engines": engines,
            "count": len(engines),
            "timestamp": "2025-12-22T00:00:00Z"
        }

    except Exception as e:
        logger.error(f"获取引擎列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")