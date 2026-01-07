#!/usr/bin/env python3
"""
分布式采集框架 - 故障容错机制
任务重试、节点故障转移和数据一致性保证
"""

import asyncio
import json
import time
import random
import threading
from typing import Dict, Any, List, Optional, Set, Tuple, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from backend.core.base import BaseScript


class FailureType(Enum):
    """故障类型"""
    NODE_DOWN = "node_down"
    TASK_TIMEOUT = "task_timeout"
    TASK_FAILED = "task_failed"
    NETWORK_ERROR = "network_error"
    RESOURCE_EXHAUSTED = "resource_exhausted"
    DATA_CORRUPTION = "data_corruption"


class RecoveryStrategy(Enum):
    """恢复策略"""
    RETRY = "retry"
    FAILOVER = "failover"
    SPLIT = "split"
    SKIP = "skip"
    MANUAL = "manual"


@dataclass
class FailureRecord:
    """故障记录"""
    failure_id: str
    task_id: str
    node_id: str
    failure_type: FailureType
    error_message: str
    timestamp: float
    retry_count: int = 0
    max_retries: int = 3
    recovery_strategy: RecoveryStrategy = RecoveryStrategy.RETRY
    status: str = "pending"  # pending, recovering, failed, resolved

    def can_retry(self) -> bool:
        """是否可以重试"""
        return self.retry_count < self.max_retries

    def mark_retry(self):
        """标记重试"""
        self.retry_count += 1
        self.timestamp = time.time()


@dataclass
class HealthCheck:
    """健康检查"""
    node_id: str
    check_type: str
    status: str  # healthy, warning, critical
    metrics: Dict[str, Any]
    timestamp: float
    response_time: float

    def is_healthy(self) -> bool:
        """是否健康"""
        return self.status == "healthy"

    def is_critical(self) -> bool:
        """是否严重故障"""
        return self.status == "critical"


class FaultToleranceManager(BaseScript):
    """故障容错管理器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 故障记录存储
        self.failure_records: Dict[str, FailureRecord] = {}

        # 健康检查存储
        self.health_checks: Dict[str, List[HealthCheck]] = {}

        # 节点状态跟踪
        self.node_status: Dict[str, str] = {}  # node_id -> status

        # 故障恢复策略
        self.recovery_strategies = {
            FailureType.NODE_DOWN: self._recover_node_down,
            FailureType.TASK_TIMEOUT: self._recover_task_timeout,
            FailureType.TASK_FAILED: self._recover_task_failed,
            FailureType.NETWORK_ERROR: self._recover_network_error,
            FailureType.RESOURCE_EXHAUSTED: self._recover_resource_exhausted,
            FailureType.DATA_CORRUPTION: self._recover_data_corruption
        }

        # 配置
        self.config = {
            'max_retry_attempts': 3,
            'retry_delay_base': 1.0,  # 基础延迟时间（秒）
            'retry_delay_max': 300.0,  # 最大延迟时间（秒）
            'health_check_interval': 30.0,  # 健康检查间隔（秒）
            'node_timeout': 120.0,  # 节点超时时间（秒）
            'task_timeout': 600.0,  # 任务超时时间（秒）
            'failover_threshold': 3,  # 故障转移阈值
            'circuit_breaker_threshold': 5,  # 熔断器阈值
            'circuit_breaker_timeout': 300.0,  # 熔断器超时时间（秒）
            'data_backup_enabled': True,
            'consistency_check_enabled': True
        }

        # 统计信息
        self.stats = {
            'total_failures': 0,
            'recovered_failures': 0,
            'unrecovered_failures': 0,
            'retry_attempts': 0,
            'successful_retries': 0,
            'failover_events': 0,
            'circuit_breaker_trips': 0,
            'health_checks': 0,
            'healthy_nodes': 0,
            'unhealthy_nodes': 0
        }

        # 熔断器状态
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}

        # 后台任务
        self.background_tasks = []

        # 依赖注入（预留）
        self.task_queue = None
        self.node_manager = None
        self.result_aggregator = None

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行故障容错操作"""
        try:
            self.logger.info(f"执行故障容错操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'report_failure':
                result = await self._report_failure(**kwargs)
            elif action == 'recover_failure':
                result = await self._recover_failure(**kwargs)
            elif action == 'health_check':
                result = await self._perform_health_check(**kwargs)
            elif action == 'get_failure_stats':
                result = await self._get_failure_stats()
            elif action == 'list_failures':
                result = await self._list_failures(**kwargs)
            elif action == 'circuit_breaker_status':
                result = await self._get_circuit_breaker_status(**kwargs)
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

    async def _report_failure(self, task_id: str, node_id: str,
                            failure_type: str, error_message: str,
                            **kwargs) -> Dict[str, Any]:
        """报告故障"""
        try:
            failure_id = f"{task_id}_{node_id}_{int(time.time())}_{random.randint(1000, 9999)}"

            failure_record = FailureRecord(
                failure_id=failure_id,
                task_id=task_id,
                node_id=node_id,
                failure_type=FailureType(failure_type),
                error_message=error_message,
                timestamp=time.time()
            )

            self.failure_records[failure_id] = failure_record
            self.stats['total_failures'] += 1

            # 更新节点状态
            self.node_status[node_id] = "unhealthy"
            self.stats['unhealthy_nodes'] = sum(1 for status in self.node_status.values() if status != "healthy")

            # 触发自动恢复
            recovery_result = await self._recover_failure(failure_id=failure_id)

            return {
                "status": "success",
                "failure_id": failure_id,
                "recovery_triggered": recovery_result.get("status") == "success"
            }

        except Exception as e:
            self.logger.error(f"报告故障失败: {e}")
            return {"status": "error", "error": f"报告故障失败: {e}"}

    async def _recover_failure(self, failure_id: str, **kwargs) -> Dict[str, Any]:
        """恢复故障"""
        try:
            if failure_id not in self.failure_records:
                return {"status": "error", "error": "故障记录不存在"}

            failure = self.failure_records[failure_id]

            if failure.status == "resolved":
                return {"status": "success", "message": "故障已解决"}

            # 获取恢复策略
            recovery_func = self.recovery_strategies.get(failure.failure_type)
            if not recovery_func:
                failure.status = "failed"
                self.stats['unrecovered_failures'] += 1
                return {"status": "error", "error": f"无恢复策略: {failure.failure_type.value}"}

            # 执行恢复
            result = await recovery_func(failure)

            if result["status"] == "success":
                failure.status = "resolved"
                self.stats['recovered_failures'] += 1

                # 更新节点状态
                if failure.node_id in self.node_status:
                    self.node_status[failure.node_id] = "healthy"
                    self.stats['healthy_nodes'] = sum(1 for status in self.node_status.values() if status == "healthy")

            else:
                failure.status = "failed"
                self.stats['unrecovered_failures'] += 1

            return result

        except Exception as e:
            self.logger.error(f"恢复故障失败: {e}")
            return {"status": "error", "error": f"恢复故障失败: {e}"}

    async def _recover_node_down(self, failure: FailureRecord) -> Dict[str, Any]:
        """恢复节点宕机"""
        try:
            # 检查熔断器
            if self._is_circuit_breaker_open(failure.node_id):
                return {"status": "error", "error": "熔断器已开启"}

            # 尝试重启节点
            if self.node_manager:
                restart_result = await self.node_manager.restart_node(failure.node_id)
                if restart_result.get("status") == "success":
                    return {"status": "success", "strategy": "node_restart"}

            # 故障转移到其他节点
            if self.task_queue:
                failover_result = await self.task_queue.failover_task(
                    failure.task_id, failure.node_id
                )
                if failover_result.get("status") == "success":
                    self.stats['failover_events'] += 1
                    return {"status": "success", "strategy": "failover"}

            return {"status": "error", "error": "无法恢复节点宕机"}

        except Exception as e:
            self.logger.error(f"恢复节点宕机失败: {e}")
            return {"status": "error", "error": f"恢复节点宕机失败: {e}"}

    async def _recover_task_timeout(self, failure: FailureRecord) -> Dict[str, Any]:
        """恢复任务超时"""
        try:
            if not failure.can_retry():
                return {"status": "error", "error": "重试次数已达上限"}

            # 指数退避重试
            delay = self._calculate_retry_delay(failure.retry_count)
            await asyncio.sleep(delay)

            # 重新提交任务
            if self.task_queue:
                retry_result = await self.task_queue.retry_task(failure.task_id)
                if retry_result.get("status") == "success":
                    failure.mark_retry()
                    self.stats['retry_attempts'] += 1
                    self.stats['successful_retries'] += 1
                    return {"status": "success", "strategy": "retry", "delay": delay}

            return {"status": "error", "error": "任务重试失败"}

        except Exception as e:
            self.logger.error(f"恢复任务超时失败: {e}")
            return {"status": "error", "error": f"恢复任务超时失败: {e}"}

    async def _recover_task_failed(self, failure: FailureRecord) -> Dict[str, Any]:
        """恢复任务失败"""
        try:
            if not failure.can_retry():
                return {"status": "error", "error": "重试次数已达上限"}

            # 检查是否为可重试错误
            if self._is_retryable_error(failure.error_message):
                delay = self._calculate_retry_delay(failure.retry_count)
                await asyncio.sleep(delay)

                if self.task_queue:
                    retry_result = await self.task_queue.retry_task(failure.task_id)
                    if retry_result.get("status") == "success":
                        failure.mark_retry()
                        self.stats['retry_attempts'] += 1
                        self.stats['successful_retries'] += 1
                        return {"status": "success", "strategy": "retry", "delay": delay}

            # 任务拆分
            if self._should_split_task(failure):
                split_result = await self._split_task(failure.task_id)
                if split_result.get("status") == "success":
                    return {"status": "success", "strategy": "split"}

            return {"status": "error", "error": "任务失败无法恢复"}

        except Exception as e:
            self.logger.error(f"恢复任务失败失败: {e}")
            return {"status": "error", "error": f"恢复任务失败失败: {e}"}

    async def _recover_network_error(self, failure: FailureRecord) -> Dict[str, Any]:
        """恢复网络错误"""
        try:
            if not failure.can_retry():
                return {"status": "error", "error": "重试次数已达上限"}

            # 网络错误通常可以重试
            delay = self._calculate_retry_delay(failure.retry_count)
            await asyncio.sleep(delay)

            if self.task_queue:
                retry_result = await self.task_queue.retry_task(failure.task_id)
                if retry_result.get("status") == "success":
                    failure.mark_retry()
                    self.stats['retry_attempts'] += 1
                    self.stats['successful_retries'] += 1
                    return {"status": "success", "strategy": "retry", "delay": delay}

            return {"status": "error", "error": "网络错误重试失败"}

        except Exception as e:
            self.logger.error(f"恢复网络错误失败: {e}")
            return {"status": "error", "error": f"恢复网络错误失败: {e}"}

    async def _recover_resource_exhausted(self, failure: FailureRecord) -> Dict[str, Any]:
        """恢复资源耗尽"""
        try:
            # 等待资源释放
            await asyncio.sleep(10)

            # 检查节点资源状态
            if self.node_manager:
                resource_check = await self.node_manager.check_node_resources(failure.node_id)
                if resource_check.get("available", False):
                    # 重新提交任务
                    if self.task_queue:
                        retry_result = await self.task_queue.retry_task(failure.task_id)
                        if retry_result.get("status") == "success":
                            return {"status": "success", "strategy": "resource_wait"}

            # 故障转移到资源充足的节点
            if self.node_manager and self.task_queue:
                available_nodes = await self.node_manager.get_available_nodes()
                if available_nodes:
                    failover_result = await self.task_queue.failover_task(
                        failure.task_id, failure.node_id, target_node=random.choice(available_nodes)
                    )
                    if failover_result.get("status") == "success":
                        self.stats['failover_events'] += 1
                        return {"status": "success", "strategy": "resource_failover"}

            return {"status": "error", "error": "资源耗尽无法恢复"}

        except Exception as e:
            self.logger.error(f"恢复资源耗尽失败: {e}")
            return {"status": "error", "error": f"恢复资源耗尽失败: {e}"}

    async def _recover_data_corruption(self, failure: FailureRecord) -> Dict[str, Any]:
        """恢复数据损坏"""
        try:
            # 尝试从备份恢复数据
            if self.config['data_backup_enabled'] and self.result_aggregator:
                restore_result = await self.result_aggregator.restore_from_backup(failure.task_id)
                if restore_result.get("status") == "success":
                    return {"status": "success", "strategy": "data_restore"}

            # 重新执行任务
            if self.task_queue:
                retry_result = await self.task_queue.retry_task(failure.task_id, force=True)
                if retry_result.get("status") == "success":
                    return {"status": "success", "strategy": "data_reexecute"}

            return {"status": "error", "error": "数据损坏无法恢复"}

        except Exception as e:
            self.logger.error(f"恢复数据损坏失败: {e}")
            return {"status": "error", "error": f"恢复数据损坏失败: {e}"}

    async def _perform_health_check(self, node_id: str, **kwargs) -> Dict[str, Any]:
        """执行健康检查"""
        try:
            start_time = time.time()

            # 模拟健康检查（实际应调用节点管理器）
            if self.node_manager:
                health_result = await self.node_manager.check_node_health(node_id)
            else:
                # 模拟检查
                health_result = {
                    "status": "healthy" if random.random() > 0.1 else "critical",
                    "metrics": {
                        "cpu_usage": random.uniform(0, 100),
                        "memory_usage": random.uniform(0, 100),
                        "disk_usage": random.uniform(0, 100),
                        "network_latency": random.uniform(0, 1000)
                    }
                }

            response_time = time.time() - start_time

            health_check = HealthCheck(
                node_id=node_id,
                check_type="comprehensive",
                status=health_result["status"],
                metrics=health_result["metrics"],
                timestamp=time.time(),
                response_time=response_time
            )

            # 存储健康检查结果
            if node_id not in self.health_checks:
                self.health_checks[node_id] = []
            self.health_checks[node_id].append(health_check)

            # 保留最近的10次检查
            if len(self.health_checks[node_id]) > 10:
                self.health_checks[node_id] = self.health_checks[node_id][-10:]

            # 更新节点状态
            self.node_status[node_id] = health_result["status"]

            # 检查熔断器
            if health_result["status"] == "critical":
                self._trip_circuit_breaker(node_id)

            self.stats['health_checks'] += 1

            return {
                "status": "success",
                "node_id": node_id,
                "health_status": health_result["status"],
                "response_time": response_time,
                "metrics": health_result["metrics"]
            }

        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return {"status": "error", "error": f"健康检查失败: {e}"}

    async def _get_failure_stats(self) -> Dict[str, Any]:
        """获取故障统计"""
        try:
            # 计算恢复率
            total_failures = self.stats['total_failures']
            recovery_rate = self.stats['recovered_failures'] / max(total_failures, 1)

            # 按类型统计故障
            failure_types = {}
            for failure in self.failure_records.values():
                failure_type = failure.failure_type.value
                if failure_type not in failure_types:
                    failure_types[failure_type] = 0
                failure_types[failure_type] += 1

            return {
                "status": "success",
                "stats": self.stats,
                "recovery_rate": recovery_rate,
                "failure_types": failure_types,
                "active_failures": len([f for f in self.failure_records.values() if f.status == "pending"])
            }

        except Exception as e:
            self.logger.error(f"获取故障统计失败: {e}")
            return {"status": "error", "error": f"获取故障统计失败: {e}"}

    async def _list_failures(self, status: str = None, limit: int = 100, **kwargs) -> Dict[str, Any]:
        """列出故障"""
        try:
            failures = []

            for failure in self.failure_records.values():
                if status and failure.status != status:
                    continue

                failures.append(asdict(failure))

            # 按时间排序
            failures.sort(key=lambda x: x['timestamp'], reverse=True)

            return {
                "status": "success",
                "total": len(failures),
                "failures": failures[:limit]
            }

        except Exception as e:
            self.logger.error(f"列出故障失败: {e}")
            return {"status": "error", "error": f"列出故障失败: {e}"}

    async def _get_circuit_breaker_status(self, node_id: str = None, **kwargs) -> Dict[str, Any]:
        """获取熔断器状态"""
        try:
            if node_id:
                breaker = self.circuit_breakers.get(node_id, {})
                return {
                    "status": "success",
                    "node_id": node_id,
                    "circuit_breaker": breaker
                }

            return {
                "status": "success",
                "circuit_breakers": self.circuit_breakers
            }

        except Exception as e:
            self.logger.error(f"获取熔断器状态失败: {e}")
            return {"status": "error", "error": f"获取熔断器状态失败: {e}"}

    def _calculate_retry_delay(self, retry_count: int) -> float:
        """计算重试延迟（指数退避）"""
        delay = self.config['retry_delay_base'] * (2 ** retry_count)
        return min(delay, self.config['retry_delay_max'])

    def _is_retryable_error(self, error_message: str) -> bool:
        """判断错误是否可重试"""
        retryable_patterns = [
            "timeout",
            "connection refused",
            "temporary failure",
            "rate limit",
            "server error"
        ]

        error_lower = error_message.lower()
        return any(pattern in error_lower for pattern in retryable_patterns)

    def _should_split_task(self, failure: FailureRecord) -> bool:
        """判断是否应该拆分任务"""
        # 简单的拆分策略：如果任务失败多次且是大数据任务
        return failure.retry_count >= 2 and "large" in failure.error_message.lower()

    async def _split_task(self, task_id: str) -> Dict[str, Any]:
        """拆分任务"""
        try:
            # 预留：实际拆分逻辑应根据任务类型实现
            if self.task_queue:
                return await self.task_queue.split_task(task_id)

            return {"status": "error", "error": "任务队列不支持拆分"}

        except Exception as e:
            self.logger.error(f"拆分任务失败: {e}")
            return {"status": "error", "error": f"拆分任务失败: {e}"}

    def _is_circuit_breaker_open(self, node_id: str) -> bool:
        """检查熔断器是否开启"""
        breaker = self.circuit_breakers.get(node_id, {})
        if not breaker.get("open", False):
            return False

        # 检查是否超时
        if time.time() - breaker.get("last_trip", 0) > self.config['circuit_breaker_timeout']:
            # 重置熔断器
            breaker["open"] = False
            breaker["failure_count"] = 0
            return False

        return True

    def _trip_circuit_breaker(self, node_id: str):
        """触发熔断器"""
        if node_id not in self.circuit_breakers:
            self.circuit_breakers[node_id] = {
                "failure_count": 0,
                "open": False,
                "last_trip": 0
            }

        breaker = self.circuit_breakers[node_id]
        breaker["failure_count"] += 1

        if breaker["failure_count"] >= self.config['circuit_breaker_threshold']:
            breaker["open"] = True
            breaker["last_trip"] = time.time()
            self.stats['circuit_breaker_trips'] += 1
            self.logger.warning(f"熔断器已开启: {node_id}")

    async def start_background_tasks(self):
        """启动后台任务"""
        # 定期健康检查
        health_check_task = asyncio.create_task(self._background_health_checks())
        self.background_tasks.append(health_check_task)

        # 故障恢复任务
        recovery_task = asyncio.create_task(self._background_failure_recovery())
        self.background_tasks.append(recovery_task)

        # 熔断器重置任务
        circuit_breaker_task = asyncio.create_task(self._background_circuit_breaker_reset())
        self.background_tasks.append(circuit_breaker_task)

    async def _background_health_checks(self):
        """后台健康检查"""
        while True:
            try:
                # 检查所有节点
                for node_id in list(self.node_status.keys()):
                    await self._perform_health_check(node_id)

                await asyncio.sleep(self.config['health_check_interval'])

            except Exception as e:
                self.logger.error(f"后台健康检查出错: {e}")
                await asyncio.sleep(60)

    async def _background_failure_recovery(self):
        """后台故障恢复"""
        while True:
            try:
                # 处理待恢复的故障
                pending_failures = [
                    fid for fid, f in self.failure_records.items()
                    if f.status == "pending"
                ]

                for failure_id in pending_failures:
                    await self._recover_failure(failure_id)

                await asyncio.sleep(30)  # 每30秒检查一次

            except Exception as e:
                self.logger.error(f"后台故障恢复出错: {e}")
                await asyncio.sleep(60)

    async def _background_circuit_breaker_reset(self):
        """后台熔断器重置"""
        while True:
            try:
                current_time = time.time()

                for node_id, breaker in self.circuit_breakers.items():
                    if (breaker.get("open", False) and
                        current_time - breaker.get("last_trip", 0) > self.config['circuit_breaker_timeout']):
                        # 重置熔断器
                        breaker["open"] = False
                        breaker["failure_count"] = 0
                        self.logger.info(f"熔断器已重置: {node_id}")

                await asyncio.sleep(60)  # 每分钟检查一次

            except Exception as e:
                self.logger.error(f"后台熔断器重置出错: {e}")
                await asyncio.sleep(60)