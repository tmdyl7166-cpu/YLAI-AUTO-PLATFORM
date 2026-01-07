#!/usr/bin/env python3
"""
AI增强智能监控系统
集成AI模型进行实时监控、异常检测和智能告警
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import psutil
import aiohttp
from pathlib import Path

from backend.core.base import BaseScript
from backend.core.registry import registry
from backend.scripts.ai_coordinator import AIModelCoordinator


@dataclass
class SystemMetrics:
    """系统指标"""
    timestamp: float
    cpu_percent: float
    memory_percent: float
    disk_usage: float
    network_io: Dict[str, Any]
    process_count: int
    load_average: tuple

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class AIModelMetrics:
    """AI模型指标"""
    model_name: str
    status: str  # 'online', 'offline', 'degraded'
    response_time: float
    request_count: int
    error_count: int
    last_check: float
    health_score: float  # 0-1

    def __post_init__(self):
        if self.last_check is None:
            self.last_check = time.time()


@dataclass
@dataclass
class Alert:
    """告警"""
    alert_id: str
    alert_type: str  # 'system', 'ai_model', 'performance', 'security'
    severity: str  # 'low', 'medium', 'high', 'critical'
    title: str
    description: str
    metrics: Dict[str, Any]
    ai_analysis: Optional[Dict[str, Any]] = None
    created_at: Optional[float] = None
    resolved_at: Optional[float] = None
    status: str = 'active'  # 'active', 'resolved', 'acknowledged'

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.metrics is None:
            self.metrics = {}


@registry.register("ai_monitor")
class AIMonitorScript(BaseScript):
    """AI增强智能监控系统"""

    name = "ai_monitor"
    description = "AI增强智能监控系统"
    version = "2.0.0"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # AI协调器
        self.ai_coordinator = None

        # 监控配置
        self.config = {
            'check_interval': 30,  # 30秒检查一次
            'alert_threshold_cpu': 80.0,
            'alert_threshold_memory': 85.0,
            'alert_threshold_disk': 90.0,
            'ai_model_timeout': 10.0,
            'max_alerts_history': 1000,
            'auto_analysis': True,
            'predictive_monitoring': True,
        }

        # 监控数据
        self.system_metrics: List[SystemMetrics] = []
        self.ai_model_metrics: Dict[str, AIModelMetrics] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alerts_history: List[Alert] = []

        # AI模型配置
        self.ai_models = {
            'qwen3:8b': {'url': 'http://localhost:11434', 'endpoint': '/api/generate'},
            'llama3.1:8b': {'url': 'http://localhost:11435', 'endpoint': '/api/generate'},
            'deepseek-r1:8b': {'url': 'http://localhost:11436', 'endpoint': '/api/generate'},
            'gpt-oss:20b': {'url': 'http://localhost:11437', 'endpoint': '/api/generate'},
        }

        # HTTP客户端
        self.session = None

    async def pre_run(self, **kwargs):
        """初始化"""
        await super().pre_run(**kwargs)

        # 初始化HTTP客户端
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10))

        # 初始化AI协调器
        try:
            self.ai_coordinator = AIModelCoordinator()
            await self.ai_coordinator.initialize()
            self.logger.info("✅ AI协调器初始化成功")
        except Exception as e:
            self.logger.warning(f"⚠️ AI协调器初始化失败: {e}")
            self.ai_coordinator = None

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        执行监控操作
        """
        try:
            if action == 'start_monitoring':
                result = await self._start_monitoring(**kwargs)
            elif action == 'get_status':
                result = await self._get_system_status()
            elif action == 'analyze_alerts':
                result = await self._analyze_alerts(**kwargs)
            elif action == 'predict_issues':
                result = await self._predict_issues(**kwargs)
            else:
                result = {"status": "error", "error": f"未知操作: {action}"}

            return result

        except Exception as e:
            self.logger.error(f"监控操作失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _start_monitoring(self, **kwargs) -> Dict[str, Any]:
        """启动监控"""
        try:
            # 启动监控循环
            monitoring_task = asyncio.create_task(self._monitoring_loop())
            alert_check_task = asyncio.create_task(self._alert_check_loop())

            # 等待一段时间让监控启动
            await asyncio.sleep(5)

            return {
                "status": "success",
                "message": "AI增强监控系统已启动",
                "monitoring_active": True,
                "ai_enhanced": bool(self.ai_coordinator)
            }

        except Exception as e:
            self.logger.error(f"启动监控失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _monitoring_loop(self):
        """监控主循环"""
        while True:
            try:
                # 收集系统指标
                await self._collect_system_metrics()

                # 检查AI模型状态
                await self._check_ai_models()

                # 清理旧数据
                self._cleanup_old_data()

                await asyncio.sleep(self.config['check_interval'])

            except Exception as e:
                self.logger.error(f"监控循环异常: {e}")
                await asyncio.sleep(10)

    async def _alert_check_loop(self):
        """告警检查循环"""
        while True:
            try:
                # 检查系统告警
                await self._check_system_alerts()

                # 检查AI模型告警
                await self._check_ai_model_alerts()

                # AI增强告警分析
                if self.config['auto_analysis'] and self.ai_coordinator:
                    await self._ai_analyze_alerts()

                await asyncio.sleep(self.config['check_interval'])

            except Exception as e:
                self.logger.error(f"告警检查异常: {e}")
                await asyncio.sleep(10)

    async def _collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)

            # 内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            disk_usage = disk.percent

            # 网络IO
            network = psutil.net_io_counters()
            network_io = {
                'bytes_sent': network.bytes_sent,
                'bytes_recv': network.bytes_recv,
                'packets_sent': network.packets_sent,
                'packets_recv': network.packets_recv
            }

            # 进程数量
            process_count = len(psutil.pids())

            # 负载平均值
            load_average = psutil.getloadavg()

            # 创建指标对象
            metrics = SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                disk_usage=disk_usage,
                network_io=network_io,
                process_count=process_count,
                load_average=load_average
            )

            self.system_metrics.append(metrics)

            # 保持最近1000个数据点
            if len(self.system_metrics) > 1000:
                self.system_metrics = self.system_metrics[-1000:]

        except Exception as e:
            self.logger.error(f"收集系统指标失败: {e}")

    async def _check_ai_models(self):
        """检查AI模型状态"""
        for model_name, config in self.ai_models.items():
            try:
                start_time = time.time()

                # 发送健康检查请求
                url = f"{config['url']}/api/tags"
                async with self.session.get(url, timeout=self.config['ai_model_timeout']) as response:
                    response_time = time.time() - start_time

                    if response.status == 200:
                        status = 'online'
                        health_score = 1.0
                    else:
                        status = 'degraded'
                        health_score = 0.5

            except Exception as e:
                response_time = time.time() - start_time
                status = 'offline'
                health_score = 0.0
                self.logger.warning(f"AI模型 {model_name} 检查失败: {e}")

            # 更新或创建指标
            if model_name not in self.ai_model_metrics:
                self.ai_model_metrics[model_name] = AIModelMetrics(
                    model_name=model_name,
                    status=status,
                    response_time=response_time,
                    request_count=1,
                    error_count=1 if status != 'online' else 0,
                    health_score=health_score
                )
            else:
                metrics = self.ai_model_metrics[model_name]
                metrics.status = status
                metrics.response_time = response_time
                metrics.request_count += 1
                if status != 'online':
                    metrics.error_count += 1
                metrics.health_score = health_score
                metrics.last_check = time.time()

    async def _check_system_alerts(self):
        """检查系统告警"""
        if not self.system_metrics:
            return

        latest = self.system_metrics[-1]

        # CPU使用率告警
        if latest.cpu_percent > self.config['alert_threshold_cpu']:
            await self._create_alert(
                alert_type='system',
                severity='high' if latest.cpu_percent > 95 else 'medium',
                title=f'CPU使用率过高: {latest.cpu_percent:.1f}%',
                description=f'系统CPU使用率超过阈值 {self.config["alert_threshold_cpu"]}%',
                metrics={'cpu_percent': latest.cpu_percent}
            )

        # 内存使用率告警
        if latest.memory_percent > self.config['alert_threshold_memory']:
            await self._create_alert(
                alert_type='system',
                severity='high' if latest.memory_percent > 95 else 'medium',
                title=f'内存使用率过高: {latest.memory_percent:.1f}%',
                description=f'系统内存使用率超过阈值 {self.config["alert_threshold_memory"]}%',
                metrics={'memory_percent': latest.memory_percent}
            )

        # 磁盘使用率告警
        if latest.disk_usage > self.config['alert_threshold_disk']:
            await self._create_alert(
                alert_type='system',
                severity='critical',
                title=f'磁盘使用率过高: {latest.disk_usage:.1f}%',
                description=f'系统磁盘使用率超过阈值 {self.config["alert_threshold_disk"]}%',
                metrics={'disk_usage': latest.disk_usage}
            )

    async def _check_ai_model_alerts(self):
        """检查AI模型告警"""
        for model_name, metrics in self.ai_model_metrics.items():
            # 离线告警
            if metrics.status == 'offline':
                await self._create_alert(
                    alert_type='ai_model',
                    severity='high',
                    title=f'AI模型离线: {model_name}',
                    description=f'AI模型 {model_name} 处于离线状态',
                    metrics={'model_name': model_name, 'status': metrics.status}
                )

            # 响应时间过长告警
            if metrics.response_time > 5.0:  # 5秒阈值
                await self._create_alert(
                    alert_type='ai_model',
                    severity='medium',
                    title=f'AI模型响应慢: {model_name}',
                    description=f'AI模型 {model_name} 响应时间过长: {metrics.response_time:.2f}s',
                    metrics={'model_name': model_name, 'response_time': metrics.response_time}
                )

            # 错误率过高告警
            if metrics.request_count > 10:
                error_rate = metrics.error_count / metrics.request_count
                if error_rate > 0.5:  # 50%错误率
                    await self._create_alert(
                        alert_type='ai_model',
                        severity='high',
                        title=f'AI模型错误率高: {model_name}',
                        description=f'AI模型 {model_name} 错误率过高: {error_rate:.2%}',
                        metrics={'model_name': model_name, 'error_rate': error_rate}
                    )

    async def _create_alert(self, alert_type: str, severity: str, title: str,
                           description: str, metrics: Dict[str, Any]):
        """创建告警"""
        alert_id = f"alert_{int(time.time())}_{hash(title) % 10000}"

        alert = Alert(
            alert_id=alert_id,
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            metrics=metrics
        )

        # 检查是否已存在相同告警
        existing_alert = None
        for active_alert in self.active_alerts.values():
            if (active_alert.alert_type == alert_type and
                active_alert.title == title and
                active_alert.status == 'active'):
                existing_alert = active_alert
                break

        if existing_alert:
            # 更新现有告警的时间戳
            existing_alert.created_at = time.time()
        else:
            # 创建新告警
            self.active_alerts[alert_id] = alert
            self.logger.warning(f"🚨 新告警: {title} ({severity})")

    async def _ai_analyze_alerts(self):
        """AI分析告警"""
        if not self.ai_coordinator or not self.active_alerts:
            return

        try:
            # 获取活跃告警
            active_alerts = list(self.active_alerts.values())

            # 准备分析数据
            alerts_data = []
            for alert in active_alerts[-10:]:  # 分析最近10个告警
                alerts_data.append({
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'description': alert.description,
                    'metrics': alert.metrics,
                    'age': time.time() - alert.created_at
                })

            analysis_prompt = f"""
            分析系统告警模式：
            告警数据: {json.dumps(alerts_data, ensure_ascii=False, indent=2)}

            请分析：
            1. 告警模式识别
            2. 潜在根本原因
            3. 影响评估
            4. 解决建议
            5. 预防措施
            """

            analysis_result = await self.ai_coordinator.run('complex_reasoning', content=analysis_prompt)

            if analysis_result.get('status') == 'success':
                ai_insights = analysis_result.get('result', {})

                # 将AI分析添加到告警中
                for alert in active_alerts:
                    if alert.alert_id in self.active_alerts:
                        self.active_alerts[alert.alert_id].ai_analysis = ai_insights

                self.logger.info("✅ AI告警分析完成")

        except Exception as e:
            self.logger.error(f"AI告警分析失败: {e}")

    async def _predict_issues(self, **kwargs) -> Dict[str, Any]:
        """预测潜在问题"""
        if not self.ai_coordinator:
            return {"status": "error", "error": "AI协调器未启用"}

        try:
            # 收集历史数据
            recent_metrics = self.system_metrics[-50:] if len(self.system_metrics) >= 50 else self.system_metrics

            # 准备预测数据
            prediction_data = {
                'system_metrics': [
                    {
                        'cpu': m.cpu_percent,
                        'memory': m.memory_percent,
                        'disk': m.disk_usage,
                        'timestamp': m.timestamp
                    } for m in recent_metrics
                ],
                'ai_models': {
                    name: {
                        'status': metrics.status,
                        'response_time': metrics.response_time,
                        'error_rate': metrics.error_count / metrics.request_count if metrics.request_count > 0 else 0
                    } for name, metrics in self.ai_model_metrics.items()
                },
                'active_alerts': len(self.active_alerts)
            }

            prediction_prompt = f"""
            基于监控数据预测潜在问题：
            监控数据: {json.dumps(prediction_data, ensure_ascii=False, indent=2)}

            请预测：
            1. 短期风险（1小时内）
            2. 中期风险（24小时内）
            3. 长期趋势
            4. 建议的预防措施
            5. 资源优化建议
            """

            result = await self.ai_coordinator.run('complex_reasoning', content=prediction_prompt)

            return result

        except Exception as e:
            self.logger.error(f"问题预测失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        try:
            latest_metrics = self.system_metrics[-1] if self.system_metrics else None

            status = {
                "status": "success",
                "timestamp": time.time(),
                "system": {
                    "cpu_percent": latest_metrics.cpu_percent if latest_metrics else 0,
                    "memory_percent": latest_metrics.memory_percent if latest_metrics else 0,
                    "disk_usage": latest_metrics.disk_usage if latest_metrics else 0,
                    "process_count": latest_metrics.process_count if latest_metrics else 0,
                },
                "ai_models": {
                    name: {
                        "status": metrics.status,
                        "response_time": metrics.response_time,
                        "health_score": metrics.health_score,
                        "last_check": metrics.last_check
                    } for name, metrics in self.ai_model_metrics.items()
                },
                "alerts": {
                    "active_count": len(self.active_alerts),
                    "active_alerts": [
                        {
                            "id": alert.alert_id,
                            "type": alert.alert_type,
                            "severity": alert.severity,
                            "title": alert.title,
                            "created_at": alert.created_at
                        } for alert in list(self.active_alerts.values())[-5:]  # 最近5个
                    ]
                },
                "ai_enhanced": bool(self.ai_coordinator)
            }

            return status

        except Exception as e:
            self.logger.error(f"获取系统状态失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _analyze_alerts(self, **kwargs) -> Dict[str, Any]:
        """分析告警模式"""
        if not self.ai_coordinator:
            return {"status": "error", "error": "AI协调器未启用"}

        try:
            # 收集告警历史
            alerts_data = []
            for alert in self.alerts_history[-50:]:  # 最近50个告警
                alerts_data.append({
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'description': alert.description,
                    'duration': (alert.resolved_at - alert.created_at) if alert.resolved_at else (time.time() - alert.created_at),
                    'status': alert.status
                })

            analysis_prompt = f"""
            分析告警模式和趋势：
            告警历史: {json.dumps(alerts_data, ensure_ascii=False, indent=2)}

            请分析：
            1. 告警类型分布
            2. 时间模式识别
            3. 根本原因分析
            4. 改进建议
            5. 预测性维护建议
            """

            result = await self.ai_coordinator.run('complex_reasoning', content=analysis_prompt)

            return result

        except Exception as e:
            self.logger.error(f"告警分析失败: {e}")
            return {"status": "error", "error": str(e)}

    def _cleanup_old_data(self):
        """清理旧数据"""
        current_time = time.time()

        # 清理30天前的系统指标
        cutoff_time = current_time - (30 * 24 * 60 * 60)  # 30天
        self.system_metrics = [
            m for m in self.system_metrics
            if m.timestamp > cutoff_time
        ]

        # 清理已解决的旧告警
        resolved_cutoff = current_time - (7 * 24 * 60 * 60)  # 7天
        alerts_to_remove = []
        for alert_id, alert in self.active_alerts.items():
            if alert.status != 'active' and alert.created_at < resolved_cutoff:
                alerts_to_remove.append(alert_id)

        for alert_id in alerts_to_remove:
            if alert_id in self.active_alerts:
                self.alerts_history.append(self.active_alerts[alert_id])
                del self.active_alerts[alert_id]

        # 限制告警历史数量
        if len(self.alerts_history) > self.config['max_alerts_history']:
            self.alerts_history = self.alerts_history[-self.config['max_alerts_history']:]

    async def post_run(self, result: Dict[str, Any]) -> None:
        """后处理"""
        await super().post_run(result)

        if self.session:
            await self.session.close()

        self.logger.info("📊 AI增强监控系统已停止")