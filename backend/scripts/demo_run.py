"""
✅ 演示脚本
功能：展示标准脚本写法
"""
from backend.core.base import BaseScript
from backend.core.registry import registry
from backend.core.logger import logger


@registry.register("demo_run")
class DemoScript(BaseScript):
    """演示脚本（展示标准写法）"""
    
    name = "demo_run"
    
    async def run(self, **kwargs):
        """
        演示脚本执行
        参数:
            message (str): 要打印的信息，默认 'Hello, YeLing!'
        返回:
            dict: 包含原始消息及处理结果
        异常:
            本脚本无异常处理，建议实际业务中补充 try/except
        """
        message = kwargs.get("message", "Hello, YeLing!")
        
        logger.info("🎯 演示脚本开始执行")
        logger.info(f"💬 接收到消息: {message}")
        
        # 模拟一些处理
        result = {
            "echo": message,
            "length": len(message),
            "upper": message.upper(),
            "lower": message.lower()
        }
        
        logger.info(f"✅ 处理完成: {result}")
        
        return result
