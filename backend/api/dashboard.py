from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Request
from backend.api.auth import get_current, require_perm
import time
from backend.services.monitoring_service import monitoring_service

router = APIRouter(prefix="/api/dashboard")

# 默认功能清单（可被超级管理员修改）
DEFAULT_FEATURES = [
    "collect",    # 采集任务
    "enum",       # 枚举任务
    "recognize",  # 识别任务
    "crack",      # 破解任务
    "logs",       # 日志管理
    "config",     # 配置默认级别
]

# 角色→可用功能矩阵（初始）
ROLE_FEATURES: Dict[str, List[str]] = {
    "superadmin": ["*"],
    "admin": DEFAULT_FEATURES,
    "user": ["collect", "enum", "recognize", "logs"],
}


@router.get("/features")
async def get_features(info: dict = Depends(get_current)):
    start_time = time.time()
    try:
        role = info.get("role", "user")
        feats = ROLE_FEATURES.get(role, [])
        if "*" in feats:
            feats = DEFAULT_FEATURES
        result = {"code": 0, "data": {"role": role, "features": feats}}
        # 记录监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/dashboard/features", 200, duration)
        return result
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("GET", "/api/dashboard/features", 500, duration)
        raise


@router.post("/roles/features")
async def set_role_features(payload: Dict, _auth=Depends(require_perm("*"))):
    """
    仅限超级管理员配置矩阵：
    { "role": "user", "features": ["collect", "logs"] }
    """
    start_time = time.time()
    try:
        role = payload.get("role")
        feats = payload.get("features")
        if not role or not isinstance(feats, list):
            # 记录无效请求监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/dashboard/roles/features", 400, duration)
            raise HTTPException(status_code=400, detail="invalid payload")
        ROLE_FEATURES[role] = feats
        result = {"code": 0, "data": {"role": role, "features": feats}}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/dashboard/roles/features", 200, duration)
        return result
    except HTTPException:
        raise
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/dashboard/roles/features", 500, duration)
        raise


@router.post("/launch")
async def launch_feature(payload: Dict, request: Request, info: dict = Depends(get_current), _perm=Depends(require_perm("launch_dashboard"))):
    """
    大屏入口统一启动接口：
    { "feature": "collect", "script": "spider", "params": { ... } }
    - 校验该用户对 feature 是否有权限
    - 通过 kernel.run(script, **params) 启动
    """
    start_time = time.time()
    try:
        role = info.get("role", "user")
        feats = ROLE_FEATURES.get(role, [])
        feature = payload.get("feature")
        script = payload.get("script")
        params = payload.get("params") or {}

        if not feature or not script:
            # 记录无效请求监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/dashboard/launch", 400, duration)
            raise HTTPException(status_code=400, detail="missing feature or script")

        if "*" not in feats and feature not in feats:
            # 记录权限拒绝监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/dashboard/launch", 403, duration)
            raise HTTPException(status_code=403, detail="forbidden feature")

        kernel = getattr(request.app.state, "kernel", None)
        if not kernel:
            # 记录服务不可用监控指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/dashboard/launch", 500, duration)
            raise HTTPException(status_code=500, detail="kernel not initialized")

        result = kernel.run(script, **params)
        response = {"code": 0, "data": {"feature": feature, "script": script, "result": result}}
        # 记录成功监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/dashboard/launch", 200, duration)
        monitoring_service.record_feature_launch(feature, script)
        return response
    except HTTPException:
        raise
    except Exception as e:
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/dashboard/launch", 500, duration)
        raise HTTPException(status_code=500, detail=f"launch failed: {e}")
