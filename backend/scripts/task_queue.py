#!/usr/bin/env python3
"""
分布式采集框架 - 任务队列系统
基于Celery + Redis的任务分发和结果收集
"""

import json
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import asyncio

from celery import Celery
from celery.result import AsyncResult
from redis import Redis
import redis

from backend.core.base import BaseScript


@dataclass
class Task:
    """任务数据结构"""
    task_id: str
    task_type: str  # 'crawl', 'analyze', 'validate', etc.
    payload: Dict[str, Any]
    priority: int = 0  # 0-255, higher = more priority
    timeout: int = 300  # seconds
    retry_count: int = 3
    retry_delay: int = 60  # seconds
    created_at: float = None
    updated_at: float = None
    status: str = 'pending'  # pending, running, completed, failed, retry
    progress: float = 0.0
    result: Any = None
    error: str = None
    worker_id: str = None
    queue_name: str = 'default'

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()


@dataclass
class TaskResult:
    """任务结果数据结构"""
    task_id: str
    status: str
    result: Any = None
    error: str = None
    execution_time: float = 0.0
    worker_id: str = None
    completed_at: float = None


class TaskQueue(BaseScript):
    """任务队列管理器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Redis配置
        self.redis_config = {
            'host': 'localhost',
            'port': 6379,
            'db': 0,
            'password': None,
            'socket_timeout': 5,
            'socket_connect_timeout': 5
        }

        # Celery配置
        self.celery_config = {
            'broker_url': 'redis://localhost:6379/0',
            'result_backend': 'redis://localhost:6379/0',
            'task_serializer': 'json',
            'result_serializer': 'json',
            'accept_content': ['json'],
            'timezone': 'UTC',
            'enable_utc': True,
            'task_default_queue': 'default',
            'task_default_exchange': 'tasks',
            'task_default_routing_key': 'task.default',
            'task_routes': {
                'task_queue.crawl_task': {'queue': 'crawl'},
                'task_queue.analyze_task': {'queue': 'analyze'},
                'task_queue.validate_task': {'queue': 'validate'},
            }
        }

        # 队列配置
        self.queues = {
            'crawl': {'max_concurrent': 10, 'priority': 5},
            'analyze': {'max_concurrent': 5, 'priority': 3},
            'validate': {'max_concurrent': 3, 'priority': 1},
            'default': {'max_concurrent': 5, 'priority': 0}
        }

        # 连接对象
        self.redis_client: Optional[Redis] = None
        self.celery_app: Optional[Celery] = None

        # 任务统计
        self.stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'running_tasks': 0,
            'avg_execution_time': 0.0,
            'queue_sizes': {}
        }

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行任务队列操作"""
        try:
            self.logger.info(f"执行任务队列操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'initialize':
                result = await self._initialize(**kwargs)
            elif action == 'submit_task':
                result = await self._submit_task(**kwargs)
            elif action == 'get_task_status':
                result = await self._get_task_status(**kwargs)
            elif action == 'cancel_task':
                result = await self._cancel_task(**kwargs)
            elif action == 'get_queue_stats':
                result = await self._get_queue_stats()
            elif action == 'cleanup_completed':
                result = await self._cleanup_completed(**kwargs)
            else:
                result = {"status": "error", "error": f"未知操作: {action}"}

            # 后运行处理
            await self.post_run(result)

            return result

        except Exception as e:
            await self.on_error(e)
            return {
                "status": "error",
                "error": str(e)
            }

    async def _initialize(self, **kwargs) -> Dict[str, Any]:
        """初始化任务队列系统"""
        try:
            # 更新配置
            self.redis_config.update(kwargs.get('redis_config', {}))
            self.celery_config.update(kwargs.get('celery_config', {}))

            # 连接Redis
            self.redis_client = redis.Redis(**self.redis_config)
            self.redis_client.ping()  # 测试连接

            # 初始化Celery应用
            self.celery_app = Celery('task_queue')
            self.celery_app.conf.update(self.celery_config)

            # 注册任务
            self._register_tasks()

            self.logger.info("任务队列系统初始化成功")

            return {
                "status": "success",
                "message": "任务队列系统初始化成功",
                "redis_connected": True,
                "celery_configured": True
            }

        except Exception as e:
            self.logger.error(f"任务队列系统初始化失败: {e}")
            return {
                "status": "error",
                "error": f"初始化失败: {e}",
                "redis_connected": False,
                "celery_configured": False
            }

    def _register_tasks(self):
        """注册Celery任务"""
        if not self.celery_app:
            return

        @self.celery_app.task(bind=True, name='task_queue.crawl_task')
        def crawl_task(self, task_data):
            """爬取任务"""
            return self._execute_task('crawl', task_data)

        @self.celery_app.task(bind=True, name='task_queue.analyze_task')
        def analyze_task(self, task_data):
            """分析任务"""
            return self._execute_task('analyze', task_data)

        @self.celery_app.task(bind=True, name='task_queue.validate_task')
        def validate_task(self, task_data):
            """验证任务"""
            return self._execute_task('validate', task_data)

    def _execute_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行具体任务（由Worker调用）"""
        try:
            start_time = time.time()

            # 这里应该调用实际的业务逻辑
            # 例如：调用风控识别、代理池、页面采集等模块

            # 模拟任务执行
            if task_type == 'crawl':
                result = self._mock_crawl_task(task_data)
            elif task_type == 'analyze':
                result = self._mock_analyze_task(task_data)
            elif task_type == 'validate':
                result = self._mock_validate_task(task_data)
            else:
                result = {"status": "error", "error": f"未知任务类型: {task_type}"}

            execution_time = time.time() - start_time

            return {
                "status": "success",
                "result": result,
                "execution_time": execution_time,
                "task_type": task_type
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "execution_time": time.time() - start_time
            }

    def _mock_crawl_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟爬取任务"""
        url = task_data.get('url', '')
        # 模拟爬取逻辑
        return {
            "url": url,
            "status_code": 200,
            "content_length": len(url) * 10,
            "crawled_at": time.time()
        }

    def _mock_analyze_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟分析任务"""
        content = task_data.get('content', '')
        # 模拟分析逻辑
        return {
            "content_length": len(content),
            "keywords_found": len(content.split()),
            "analyzed_at": time.time()
        }

    def _mock_validate_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """模拟验证任务"""
        data = task_data.get('data', {})
        # 模拟验证逻辑
        return {
            "is_valid": True,
            "validation_score": 0.95,
            "validated_at": time.time()
        }

    async def _submit_task(self, task_type: str, payload: Dict[str, Any],
                          priority: int = 0, timeout: int = 300,
                          queue_name: str = 'default', **kwargs) -> Dict[str, Any]:
        """提交任务到队列"""
        try:
            task = Task(
                task_id=str(uuid.uuid4()),
                task_type=task_type,
                payload=payload,
                priority=priority,
                timeout=timeout,
                queue_name=queue_name
            )

            # 存储任务到Redis
            task_key = f"task:{task.task_id}"
            self.redis_client.setex(
                task_key,
                86400,  # 24小时过期
                json.dumps(asdict(task))
            )

            # 提交到Celery
            if self.celery_app:
                celery_task_name = f'task_queue.{task_type}_task'
                celery_task = self.celery_app.send_task(
                    celery_task_name,
                    args=[asdict(task)],
                    queue=queue_name,
                    priority=priority,
                    time_limit=timeout
                )

                # 更新任务状态
                task.status = 'submitted'
                task.updated_at = time.time()
                self.redis_client.setex(task_key, 86400, json.dumps(asdict(task)))

                # 更新统计
                self.stats['total_tasks'] += 1

                return {
                    "status": "success",
                    "task_id": task.task_id,
                    "celery_task_id": celery_task.id,
                    "queue": queue_name,
                    "estimated_wait_time": self._estimate_wait_time(queue_name)
                }
            else:
                return {"status": "error", "error": "Celery应用未初始化"}

        except Exception as e:
            self.logger.error(f"提交任务失败: {e}")
            return {"status": "error", "error": f"提交任务失败: {e}"}

    async def _get_task_status(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """获取任务状态"""
        try:
            task_key = f"task:{task_id}"
            task_data = self.redis_client.get(task_key)

            if not task_data:
                return {"status": "error", "error": "任务不存在"}

            task = Task(**json.loads(task_data))

            # 如果有Celery任务ID，获取Celery状态
            celery_status = None
            if hasattr(task, 'celery_task_id') and task.celery_task_id:
                try:
                    celery_result = AsyncResult(task.celery_task_id, app=self.celery_app)
                    celery_status = {
                        "state": celery_result.state,
                        "current": celery_result.current,
                        "total": celery_result.total,
                        "result": celery_result.result if celery_result.ready() else None
                    }
                except Exception as e:
                    self.logger.warning(f"获取Celery状态失败: {e}")

            return {
                "status": "success",
                "task": asdict(task),
                "celery_status": celery_status
            }

        except Exception as e:
            self.logger.error(f"获取任务状态失败: {e}")
            return {"status": "error", "error": f"获取任务状态失败: {e}"}

    async def _cancel_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """取消任务"""
        try:
            task_key = f"task:{task_id}"
            task_data = self.redis_client.get(task_key)

            if not task_data:
                return {"status": "error", "error": "任务不存在"}

            task = Task(**json.loads(task_data))

            # 取消Celery任务
            if hasattr(task, 'celery_task_id') and task.celery_task_id:
                try:
                    celery_result = AsyncResult(task.celery_task_id, app=self.celery_app)
                    celery_result.revoke(terminate=True)
                except Exception as e:
                    self.logger.warning(f"取消Celery任务失败: {e}")

            # 更新任务状态
            task.status = 'cancelled'
            task.updated_at = time.time()
            self.redis_client.setex(task_key, 86400, json.dumps(asdict(task)))

            return {
                "status": "success",
                "task_id": task_id,
                "message": "任务已取消"
            }

        except Exception as e:
            self.logger.error(f"取消任务失败: {e}")
            return {"status": "error", "error": f"取消任务失败: {e}"}

    async def _get_queue_stats(self) -> Dict[str, Any]:
        """获取队列统计信息"""
        try:
            stats = dict(self.stats)

            # 获取各队列长度
            for queue_name in self.queues.keys():
                try:
                    queue_length = self.redis_client.llen(f"celery:{queue_name}")
                    stats['queue_sizes'][queue_name] = queue_length
                except:
                    stats['queue_sizes'][queue_name] = 0

            # 获取活跃任务数
            try:
                active_tasks = self.celery_app.control.inspect().active()
                stats['active_tasks'] = active_tasks or {}
            except:
                stats['active_tasks'] = {}

            return {
                "status": "success",
                "stats": stats,
                "timestamp": time.time()
            }

        except Exception as e:
            self.logger.error(f"获取队列统计失败: {e}")
            return {"status": "error", "error": f"获取队列统计失败: {e}"}

    async def _cleanup_completed(self, max_age: int = 3600, **kwargs) -> Dict[str, Any]:
        """清理已完成的任务"""
        try:
            cleaned_count = 0

            # 扫描所有任务键
            task_keys = self.redis_client.keys("task:*")

            for task_key in task_keys:
                try:
                    task_data = self.redis_client.get(task_key)
                    if task_data:
                        task = Task(**json.loads(task_data))

                        # 检查是否可以清理
                        if (task.status in ['completed', 'failed', 'cancelled'] and
                            time.time() - task.updated_at > max_age):
                            self.redis_client.delete(task_key)
                            cleaned_count += 1

                except Exception as e:
                    self.logger.warning(f"清理任务失败: {e}")

            return {
                "status": "success",
                "cleaned_count": cleaned_count,
                "message": f"清理了 {cleaned_count} 个过期任务"
            }

        except Exception as e:
            self.logger.error(f"清理任务失败: {e}")
            return {"status": "error", "error": f"清理任务失败: {e}"}

    def _estimate_wait_time(self, queue_name: str) -> float:
        """估算等待时间"""
        try:
            queue_length = self.redis_client.llen(f"celery:{queue_name}")
            avg_execution_time = self.stats.get('avg_execution_time', 30)  # 默认30秒

            # 简单估算：队列长度 * 平均执行时间 / 并发数
            concurrent = self.queues.get(queue_name, {}).get('max_concurrent', 1)
            estimated_time = (queue_length * avg_execution_time) / max(concurrent, 1)

            return round(estimated_time, 1)

        except:
            return 0.0

    async def submit_batch_tasks(self, tasks: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """批量提交任务"""
        results = []

        for task_data in tasks:
            result = await self._submit_task(**task_data, **kwargs)
            results.append(result)

        successful = len([r for r in results if r['status'] == 'success'])

        return {
            "status": "success",
            "total_tasks": len(tasks),
            "successful_submissions": successful,
            "failed_submissions": len(tasks) - successful,
            "results": results
        }

    async def get_batch_status(self, task_ids: List[str]) -> Dict[str, Any]:
        """批量获取任务状态"""
        results = []

        for task_id in task_ids:
            result = await self._get_task_status(task_id)
            results.append(result)

        return {
            "status": "success",
            "total_tasks": len(task_ids),
            "results": results
        }