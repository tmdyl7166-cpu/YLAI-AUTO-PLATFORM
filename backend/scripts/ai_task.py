"""
✅ AI任务脚本示例
功能：调用AI模型处理任务
"""
from backend.core.base import BaseScript
from backend.core.registry import registry
from backend.core.logger import logger


@registry.register("ai_task")
class AITaskScript(BaseScript):
    """AI任务处理脚本"""
    
    name = "ai_task"
    
    async def run(self, **kwargs):
        """
        执行AI任务
        参数:
            prompt (str): 输入给AI的提示词
            model (str): 使用的AI模型名称,默认 'gpt-3.5-turbo'
        返回:
            dict: 任务执行结果
        异常:
            捕获所有异常并记录日志,返回失败信息
        """
        prompt = kwargs.get("prompt", "")
        model = kwargs.get("model", "gpt-3.5-turbo")
        
        logger.info(f"🤖 启动AI任务,模型: {model}")
        logger.info(f"📝 输入提示: {prompt}")
        
        try:
            # 这里是AI调用逻辑（示例）
            logger.info("⏳ AI处理中...")
            
            # 示例：调用OpenAI API
            # import openai
            # response = openai.ChatCompletion.create(
            #     model=model,
            #     messages=[{"role": "user", "content": prompt}]
            # )
            # result = response.choices[0].message.content
            
            # 模拟AI响应
            result = f"AI已处理您的请求: {prompt[:50]}..."
            
            logger.info(f"✅ AI任务完成")
            return {"status": "success", "result": result}
            
        except Exception as e:
            logger.error(f"❌ AI任务失败: {e}")
            return {"status": "failed", "error": str(e)}
