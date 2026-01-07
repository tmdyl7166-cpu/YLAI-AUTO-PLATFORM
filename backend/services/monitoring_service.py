"""
监控服务模块
集成Prometheus指标收集和系统监控
"""
import time
import psutil
import asyncio
from typing import Dict, Any, Optional
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    generate_latest, CONTENT_TYPE_LATEST
)
from prometheus_client.core import CollectorRegistry
import structlog

from backend.services.performance_monitor import performance_monitor
from backend.services.cache_service import cache_service
from backend.services.database_service import db_service

logger = structlog.get_logger(__name__)

class MonitoringService:
    """监控服务类"""

    def __init__(self):
        self.registry = CollectorRegistry()
        self._init_metrics()
        self._start_time = time.time()

    def _init_metrics(self):
        """初始化Prometheus指标"""

        # API请求指标
        self.api_requests_total = Counter(
            'ylai_api_requests_total',
            'Total number of API requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )

        self.api_request_duration = Histogram(
            'ylai_api_request_duration_seconds',
            'API request duration in seconds',
            ['method', 'endpoint'],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
            registry=self.registry
        )

        # 业务指标
        self.pipeline_runs_total = Counter(
            'ylai_pipeline_runs_total',
            'Total number of pipeline runs',
            ['status'],
            registry=self.registry
        )

        self.phone_analysis_total = Counter(
            'ylai_phone_analysis_total',
            'Total number of phone analysis requests',
            ['result'],
            registry=self.registry
        )

        self.ai_tasks_total = Counter(
            'ylai_ai_tasks_total',
            'Total number of AI tasks',
            ['status'],
            registry=self.registry
        )

        # 缓存指标
        self.cache_hits_total = Counter(
            'ylai_cache_hits_total',
            'Total number of cache hits',
            registry=self.registry
        )

        self.cache_misses_total = Counter(
            'ylai_cache_misses_total',
            'Total number of cache misses',
            registry=self.registry
        )

        self.cache_size = Gauge(
            'ylai_cache_size',
            'Current cache size',
            registry=self.registry
        )

        # 数据库指标
        self.db_connections_active = Gauge(
            'ylai_db_connections_active',
            'Number of active database connections',
            registry=self.registry
        )

        self.db_query_duration = Histogram(
            'ylai_db_query_duration_seconds',
            'Database query duration in seconds',
            ['operation'],
            buckets=(0.01, 0.05, 0.1, 0.5, 1.0),
            registry=self.registry
        )

        # 系统指标
        self.system_cpu_usage = Gauge(
            'ylai_system_cpu_usage_percent',
            'System CPU usage percentage',
            registry=self.registry
        )

        self.system_memory_usage = Gauge(
            'ylai_system_memory_usage_bytes',
            'System memory usage in bytes',
            registry=self.registry
        )

        self.system_disk_usage = Gauge(
            'ylai_system_disk_usage_bytes',
            'System disk usage in bytes',
            ['mount_point'],
            registry=self.registry
        )

        # 应用指标
        self.app_uptime = Gauge(
            'ylai_app_uptime_seconds',
            'Application uptime in seconds',
            registry=self.registry
        )

        self.app_active_connections = Gauge(
            'ylai_app_active_connections',
            'Number of active connections',
            registry=self.registry
        )

        # 服务健康状态
        self.service_health = Gauge(
            'ylai_service_health',
            'Service health status (1=healthy, 0=unhealthy)',
            ['service'],
            registry=self.registry
        )

        # 版本信息
        self.app_info = Info(
            'ylai_app_info',
            'Application information',
            registry=self.registry
        )

    async def collect_system_metrics(self):
        """收集系统指标"""
        try:
            # CPU使用率
            cpu_percent = psutil.cpu_percent(interval=1)
            self.system_cpu_usage.set(cpu_percent)

            # 内存使用率
            memory = psutil.virtual_memory()
            self.system_memory_usage.set(memory.used)

            # 磁盘使用率
            disk_usage = psutil.disk_usage('/')
            self.system_disk_usage.labels(mount_point='/').set(disk_usage.used)

            # 应用运行时间
            self.app_uptime.set(time.time() - self._start_time)

        except Exception as e:
            logger.error("Failed to collect system metrics", error=str(e))

    async def collect_service_metrics(self):
        """收集服务指标"""
        try:
            # 缓存服务健康状态
            cache_health = await self._check_cache_health()
            self.service_health.labels(service='cache').set(1 if cache_health else 0)

            # 数据库服务健康状态
            db_health = await self._check_database_health()
            self.service_health.labels(service='database').set(1 if db_health else 0)

            # 缓存大小
            cache_size = len(cache_service.memory_cache)
            self.cache_size.set(cache_size)

        except Exception as e:
            logger.error("Failed to collect service metrics", error=str(e))

    async def _check_cache_health(self) -> bool:
        """检查缓存服务健康状态"""
        try:
            return cache_service.health_check().get('available', False)
        except Exception:
            return False

    async def _check_database_health(self) -> bool:
        """检查数据库服务健康状态"""
        try:
            return db_service.health_check().get('available', False)
        except Exception:
            return False

    def record_api_request(self, method: str, endpoint: str, status: int, duration: float):
        """记录API请求"""
        self.api_requests_total.labels(
            method=method,
            endpoint=endpoint,
            status=str(status)
        ).inc()

        self.api_request_duration.labels(
            method=method,
            endpoint=endpoint
        ).observe(duration)

    def record_pipeline_run(self, status: str):
        """记录流水线运行"""
        self.pipeline_runs_total.labels(status=status).inc()

    def record_phone_analysis(self, result: str):
        """记录号码分析"""
        self.phone_analysis_total.labels(result=result).inc()

    def record_cache_hit(self):
        """记录缓存命中"""
        self.cache_hits_total.inc()

    def record_cache_miss(self):
        """记录缓存未命中"""
        self.cache_misses_total.inc()

    def record_db_query(self, operation: str, duration: float):
        """记录数据库查询"""
        self.db_query_duration.labels(operation=operation).observe(duration)

    def record_ai_task(self, status: str):
        """记录AI任务执行结果"""
        self.ai_tasks_total.labels(status=status).inc()

    def get_metrics(self) -> str:
        """获取Prometheus格式的指标"""
        return generate_latest(self.registry).decode('utf-8')

    async def start_collection(self):
        """启动指标收集"""
        logger.info("Starting metrics collection")

        # 设置应用信息
        self.app_info.info({
            'version': '1.0.0',
            'environment': 'development'
        })

        # 启动定期收集任务
        asyncio.create_task(self._collection_loop())

    async def _collection_loop(self):
        """指标收集循环"""
        while True:
            try:
                await self.collect_system_metrics()
                await self.collect_service_metrics()
                await asyncio.sleep(30)  # 每30秒收集一次
            except Exception as e:
                logger.error("Metrics collection error", error=str(e))
                await asyncio.sleep(30)

# 全局监控服务实例
monitoring_service = MonitoringService()