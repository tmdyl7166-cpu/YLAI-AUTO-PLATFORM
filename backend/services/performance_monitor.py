import asyncio
import time
from functools import wraps
from typing import Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)

class PerformanceMonitor:
    def __init__(self):
        self.metrics: Dict[str, Dict[str, Any]] = {}

    def monitor_sync(self, name: str):
        def decorator(func: Callable):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.record_metric(name, execution_time, success=True)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.record_metric(name, execution_time, success=False, error=str(e))
                    raise
            return wrapper
        return decorator

    async def monitor_async(self, name: str):
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = await func(*args, **kwargs)
                    execution_time = time.time() - start_time
                    self.record_metric(name, execution_time, success=True)
                    return result
                except Exception as e:
                    execution_time = time.time() - start_time
                    self.record_metric(name, execution_time, success=False, error=str(e))
                    raise
            return wrapper
        return decorator

    def record_metric(self, name: str, execution_time: float, success: bool, error: str = None):
        if name not in self.metrics:
            self.metrics[name] = {
                'calls': 0,
                'total_time': 0,
                'avg_time': 0,
                'min_time': float('inf'),
                'max_time': 0,
                'success_count': 0,
                'error_count': 0,
                'last_errors': []
            }

        metric = self.metrics[name]
        metric['calls'] += 1
        metric['total_time'] += execution_time
        metric['avg_time'] = metric['total_time'] / metric['calls']
        metric['min_time'] = min(metric['min_time'], execution_time)
        metric['max_time'] = max(metric['max_time'], execution_time)

        if success:
            metric['success_count'] += 1
        else:
            metric['error_count'] += 1
            if error and len(metric['last_errors']) < 5:
                metric['last_errors'].append(error)

    def get_metrics(self) -> Dict[str, Dict[str, Any]]:
        return self.metrics.copy()

    def reset_metrics(self):
        self.metrics.clear()

# 全局性能监控实例
performance_monitor = PerformanceMonitor()