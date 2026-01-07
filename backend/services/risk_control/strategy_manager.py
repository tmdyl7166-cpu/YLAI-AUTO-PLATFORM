"""
策略管理器 - 风控策略自动切换
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class StrategyType(Enum):
    NORMAL = "normal"
    STEALTH = "stealth"
    AGGRESSIVE = "aggressive"
    ROTATION = "rotation"
    BACKOFF = "backoff"

@dataclass
class StrategyResult:
    """策略执行结果"""
    strategy: StrategyType
    success: bool
    response_time: float
    risk_detected: bool
    risk_type: str
    timestamp: datetime
    metadata: Dict[str, Any]

class StrategyManager:
    """风控策略管理器"""

    def __init__(self):
        self.strategies = {
            StrategyType.NORMAL: self._normal_strategy,
            StrategyType.STEALTH: self._stealth_strategy,
            StrategyType.AGGRESSIVE: self._aggressive_strategy,
            StrategyType.ROTATION: self._rotation_strategy,
            StrategyType.BACKOFF: self._backoff_strategy
        }

        self.current_strategy = StrategyType.NORMAL
        self.history: List[StrategyResult] = []
        self.failure_count = 0
        self.last_failure_time = None

        # 策略切换阈值
        self.max_failures = 3
        self.backoff_time = 60  # 秒
        self.strategy_timeout = 300  # 5分钟

    def execute_with_strategy(self, action: Callable, *args, **kwargs) -> Dict[str, Any]:
        """
        使用当前策略执行动作

        Args:
            action: 要执行的动作函数
            *args: 动作参数
            **kwargs: 动作关键字参数

        Returns:
            执行结果
        """
        start_time = time.time()
        strategy = self._select_strategy()

        try:
            logger.info(f"使用策略 {strategy.value} 执行动作")

            # 执行动作
            result = action(*args, **kwargs)

            # 记录成功结果
            self._record_result(strategy, True, time.time() - start_time,
                              result.get('risk_detected', False),
                              result.get('risk_type', 'none'), result)

            # 重置失败计数
            self.failure_count = 0

            return result

        except Exception as e:
            execution_time = time.time() - start_time

            # 记录失败结果
            self._record_result(strategy, False, execution_time, True, 'error', {'error': str(e)})

            # 增加失败计数
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            logger.warning(f"策略 {strategy.value} 执行失败: {e}")

            # 尝试切换策略
            if self.failure_count >= self.max_failures:
                self._switch_strategy()
                logger.info(f"切换到新策略: {self.current_strategy.value}")

            raise e

    def _select_strategy(self) -> StrategyType:
        """选择合适的策略"""
        now = datetime.now()

        # 如果在backoff期间，使用backoff策略
        if (self.last_failure_time and
            now - self.last_failure_time < timedelta(seconds=self.backoff_time)):
            return StrategyType.BACKOFF

        # 基于历史表现选择策略
        if self.history:
            recent_results = [r for r in self.history
                            if now - r.timestamp < timedelta(minutes=5)]

            if recent_results:
                success_rate = sum(1 for r in recent_results if r.success) / len(recent_results)

                if success_rate < 0.3:
                    return StrategyType.STEALTH
                elif success_rate > 0.8:
                    return StrategyType.AGGRESSIVE

        return self.current_strategy

    def _switch_strategy(self):
        """切换策略"""
        strategy_order = [
            StrategyType.NORMAL,
            StrategyType.STEALTH,
            StrategyType.ROTATION,
            StrategyType.AGGRESSIVE
        ]

        current_index = strategy_order.index(self.current_strategy)
        next_index = (current_index + 1) % len(strategy_order)
        self.current_strategy = strategy_order[next_index]

        logger.info(f"策略切换: {strategy_order[current_index].value} -> {self.current_strategy.value}")

    def _record_result(self, strategy: StrategyType, success: bool,
                      response_time: float, risk_detected: bool,
                      risk_type: str, metadata: Dict[str, Any]):
        """记录执行结果"""
        result = StrategyResult(
            strategy=strategy,
            success=success,
            response_time=response_time,
            risk_detected=risk_detected,
            risk_type=risk_type,
            timestamp=datetime.now(),
            metadata=metadata
        )

        self.history.append(result)

        # 保持历史记录在合理大小
        if len(self.history) > 100:
            self.history = self.history[-50:]

    def _normal_strategy(self, action: Callable, *args, **kwargs) -> Dict[str, Any]:
        """正常策略 - 标准请求"""
        return action(*args, **kwargs)

    def _stealth_strategy(self, action: Callable, *args, **kwargs) -> Dict[str, Any]:
        """隐秘策略 - 降低频率，增加延迟"""
        time.sleep(2)  # 增加延迟
        return action(*args, **kwargs)

    def _aggressive_strategy(self, action: Callable, *args, **kwargs) -> Dict[str, Any]:
        """激进策略 - 提高并发，减少延迟"""
        # 可以在这里实现并发请求等
        return action(*args, **kwargs)

    def _rotation_strategy(self, action: Callable, *args, **kwargs) -> Dict[str, Any]:
        """轮换策略 - 轮换代理、UA等"""
        # 这里可以集成代理轮换逻辑
        return action(*args, **kwargs)

    def _backoff_strategy(self, action: Callable, *args, **kwargs) -> Dict[str, Any]:
        """退避策略 - 暂停请求"""
        remaining_time = 0
        if self.last_failure_time:
            elapsed = (datetime.now() - self.last_failure_time).total_seconds()
            remaining_time = max(0, self.backoff_time - elapsed)

        if remaining_time > 0:
            logger.info(f"退避策略: 等待 {remaining_time:.1f} 秒")
            time.sleep(remaining_time)

        return action(*args, **kwargs)

    def get_strategy_stats(self) -> Dict[str, Any]:
        """获取策略统计信息"""
        if not self.history:
            return {"total_executions": 0}

        total = len(self.history)
        successful = sum(1 for r in self.history if r.success)
        avg_response_time = sum(r.response_time for r in self.history) / total

        strategy_counts = {}
        for result in self.history:
            strategy = result.strategy.value
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1

        return {
            "total_executions": total,
            "success_rate": successful / total,
            "avg_response_time": avg_response_time,
            "current_strategy": self.current_strategy.value,
            "failure_count": self.failure_count,
            "strategy_distribution": strategy_counts
        }

    def reset(self):
        """重置策略管理器"""
        self.current_strategy = StrategyType.NORMAL
        self.history.clear()
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("策略管理器已重置")