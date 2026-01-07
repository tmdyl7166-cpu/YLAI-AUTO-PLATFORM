"""
✅ 号码逆向分析脚本
功能：通过号码进行数据反推
"""
from backend.core.base import BaseScript
from backend.core.registry import registry
from backend.core.logger import logger
from backend.services.cache_service import cache_service
from backend.services.database_service import db_service


@registry.register("phone_reverse")
class PhoneReverseScript(BaseScript):
    """号码逆向分析脚本"""

    name = "phone_reverse"

    async def run(self, **kwargs):
        """
        执行号码逆向分析
        参数:
            phone (str): 要分析的手机号码，默认 '13800138000'
        返回:
            dict: 包含分析结果
        异常:
            捕获所有异常并记录日志
        """
        phone = kwargs.get("phone", "13800138000")

        # 输入验证
        if not phone or not isinstance(phone, str):
            raise ValueError("Phone number is required and must be a string")

        phone = phone.strip()
        if not phone:
            raise ValueError("Phone number cannot be empty")

        if not phone.isdigit():
            raise ValueError("Phone number must contain only digits")

        if len(phone) != 11:
            raise ValueError("Phone number must be exactly 11 digits")

        logger.info(f"📞 开始号码逆向分析: {phone}")

        # 尝试从缓存获取
        cache_key = f"phone_analysis:{phone}"
        cached_result = cache_service.get(cache_key)
        if cached_result:
            logger.info(f"✅ 从缓存获取号码分析结果: {phone}")
            return {"status": "success", "data": cached_result, "cached": True}

        # 尝试从数据库获取
        db_result = db_service.get_phone_cache(phone)
        if db_result:
            logger.info(f"✅ 从数据库获取号码分析结果: {phone}")
            # 存入缓存
            cache_service.set(cache_key, db_result, ttl=86400)  # 24小时
            return {"status": "success", "data": db_result, "cached": True}

        try:
            # 这里实现号码逆向分析逻辑
            # 示例：模拟分析结果
            result = {
                "phone": phone,
                "carrier": "中国移动",  # 模拟运营商
                "province": "北京",    # 模拟省份
                "city": "北京",        # 模拟城市
                "area_code": "010",    # 模拟区号
                "post_code": "100000", # 模拟邮编
                "analysis_time": "2025-12-20T10:00:00Z"
            }

            # 存入数据库
            db_service.set_phone_cache(phone, result)

            # 存入缓存
            cache_service.set(cache_key, result, ttl=86400)  # 24小时

            logger.info(f"✅ 分析完成并缓存: {phone}")
            return {"status": "success", "data": result}

        except Exception as e:
            logger.error(f"❌ 分析失败: {e}")
            return {"status": "failed", "error": str(e)}