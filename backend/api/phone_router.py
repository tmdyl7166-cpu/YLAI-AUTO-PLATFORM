"""
Phone Analysis API Router
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.core.registry import registry
from backend.api.auth import require_perm
from backend.core.logger import api_logger
from backend.services.cache_service import cache_service
from backend.services.database_service import db_service
from backend.services.monitoring_service import monitoring_service
import traceback
import json
import time

router = APIRouter()

@router.post("/api/phone/analyze")
async def analyze_phone(
    data: dict,
    user=Depends(require_perm("run"))
):
    """
    号码逆向分析接口

    请求体参数:
    - phone: str, 必需，手机号码

    返回:
    - status: str, 成功状态
    - data: dict, 分析结果包含运营商、省份、城市等信息
    """
    start_time = time.time()
    result_status = "success"

    try:
        phone = data.get("phone", "").strip()

        if not phone:
            api_logger.warning(f"Phone analysis: empty phone number from user {user.get('username')}")
            raise HTTPException(status_code=400, detail="Phone number is required")

        if not phone.isdigit() or len(phone) != 11:
            api_logger.warning(f"Phone analysis: invalid phone format '{phone}' from user {user.get('username')}")
            raise HTTPException(status_code=400, detail="Invalid phone number format (must be 11 digits)")

        api_logger.info(f"Phone analysis: analyzing {phone} for user {user.get('username')}")

        # 首先检查缓存
        cache_key = f"phone_analysis:{phone}"
        cached_result = await cache_service.get(cache_key)
        if cached_result:
            api_logger.info(f"Phone analysis: cache hit for {phone}")
            # 记录缓存命中
            monitoring_service.record_cache_hit()
            # 记录API请求指标
            duration = time.time() - start_time
            monitoring_service.record_api_request("POST", "/api/phone/analyze", 200, duration)
            monitoring_service.record_phone_analysis("cache_hit")
            # 记录API调用到数据库
            await db_service.log_api_call(
                endpoint="/api/phone/analyze",
                method="POST",
                user_id=user.get('id'),
                status_code=200,
                response_size=len(json.dumps(cached_result)),
                cache_hit=True
            )
            return cached_result

        # 调用注册的脚本
        script = registry.get("phone_reverse")
        if not script:
            api_logger.error("Phone analysis: script 'phone_reverse' not found in registry")
            raise HTTPException(status_code=500, detail="Phone analysis service unavailable")

        result = await script.run(phone=phone)

        # 缓存结果（24小时）
        if result.get("status") == "success":
            await cache_service.set(cache_key, result, ttl=86400)  # 24小时

            # 存储到数据库
            await db_service.cache_phone_analysis(phone, result)

        # 记录API调用
        await db_service.log_api_call(
            endpoint="/api/phone/analyze",
            method="POST",
            user_id=user.get('id'),
            status_code=200,
            response_size=len(json.dumps(result)),
            cache_hit=False
        )

        api_logger.info(f"Phone analysis: completed for {phone}, result: {result.get('status')}")
        # 记录监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/phone/analyze", 200, duration)
        monitoring_service.record_phone_analysis("success")
        return result

    except HTTPException:
        raise
    except Exception as e:
        result_status = "error"
        error_msg = f"Phone analysis failed: {str(e)}"
        api_logger.error(f"{error_msg}\n{traceback.format_exc()}")
        # 记录错误监控指标
        duration = time.time() - start_time
        monitoring_service.record_api_request("POST", "/api/phone/analyze", 500, duration)
        monitoring_service.record_phone_analysis("error")
        raise HTTPException(status_code=500, detail="Internal server error during phone analysis")