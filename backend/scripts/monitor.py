"""
✅ 监控脚本示例
功能：系统状态监控
"""
import time
from backend.core.base import BaseScript
from backend.core.registry import registry
from backend.core.logger import logger


@registry.register("monitor")
class MonitorScript(BaseScript):
    """系统监控脚本"""
    
    name = "monitor"
    
    async def run(self, **kwargs):
        """
        执行监控任务
        参数:
            duration (int): 监控总时长（秒），默认 10
            interval (int): 检查间隔（秒），默认 2
        返回:
            dict: 包含检查次数和状态
        异常:
            捕获 KeyboardInterrupt 和所有异常，记录日志并返回状态
        """
        duration = kwargs.get("duration", 10)
        interval = kwargs.get("interval", 2)
        
        logger.info(f"📊 启动系统监控，持续 {duration} 秒，间隔 {interval} 秒")
        
        try:
            start_time = time.time()
            count = 0
            
            while time.time() - start_time < duration:
                count += 1
                
                # 这里是监控逻辑（示例）
                # 例如：检查CPU、内存、磁盘等
                logger.info(f"🔍 监控检查 #{count}: 系统正常")
                
                time.sleep(interval)
            
            logger.info(f"✅ 监控完成，共检查 {count} 次")
            return {"status": "success", "checks": count}
            
        except KeyboardInterrupt:
            logger.warning("⚠️ 监控被用户中断")
            return {"status": "interrupted"}
        except Exception as e:
            logger.error(f"❌ 监控失败: {e}")
            return {"status": "failed", "error": str(e)}
