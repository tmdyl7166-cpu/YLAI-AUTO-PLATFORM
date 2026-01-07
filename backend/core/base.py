from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import asyncio
import time
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class BaseScript(ABC):
    """脚本基类 - 提供统一的脚本执行框架"""

    name = "base"
    description = "基础脚本"
    version = "1.0.0"
    timeout = 30  # 默认30秒超时

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.execution_id = None
        self.resources = []
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    async def run(self, **kwargs) -> Dict[str, Any]:
        """执行脚本的主要逻辑"""
        raise NotImplementedError("必须实现 run 方法")

    async def pre_run(self, **kwargs) -> None:
        """执行前的准备工作"""
        self.start_time = time.time()
        logger.info(f"脚本 {self.name} 开始执行")

    async def post_run(self, result: Dict[str, Any]) -> None:
        """执行后的清理工作"""
        self.end_time = time.time()
        execution_time = self.end_time - self.start_time
        logger.info(f"脚本 {self.name} 执行完成，耗时: {execution_time:.2f}秒")
    async def on_error(self, error: Exception) -> None:
        """错误处理钩子"""
        logger.error(f"脚本 {self.name} 执行出错: {str(error)}")
        await self.cleanup()

    async def cleanup(self) -> None:
        """资源清理"""
        for resource in self.resources:
            try:
                if hasattr(resource, 'close'):
                    await resource.close()
                elif hasattr(resource, 'cleanup'):
                    await resource.cleanup()
            except Exception as e:
                logger.warning(f"清理资源时出错: {e}")
        self.resources.clear()

    def validate_params(self, **kwargs) -> Dict[str, Any]:
        """参数验证和类型转换"""
        return kwargs

    @asynccontextmanager
    async def execution_context(self, **kwargs):
        """执行上下文管理器"""
        try:
            await self.pre_run(**kwargs)
            yield
            # result会在外部获取
        except Exception as e:
            await self.on_error(e)
            raise
        finally:
            await self.cleanup()

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """统一的执行入口"""
        # 参数验证
        validated_kwargs = self.validate_params(**kwargs)

        # 执行超时控制
        try:
            async with self.execution_context(**validated_kwargs):
                result = await asyncio.wait_for(
                    self.run(**validated_kwargs),
                    timeout=self.timeout
                )
                await self.post_run(result)
                return result
        except asyncio.TimeoutError:
            error_msg = f"脚本 {self.name} 执行超时 ({self.timeout}秒)"
            logger.error(error_msg)
            await self.on_error(TimeoutError(error_msg))
            return {
                "success": False,
                "error": error_msg,
                "timeout": self.timeout
            }
        except Exception as e:
            await self.on_error(e)
            return {
                "success": False,
                "error": str(e)
            }
