#!/usr/bin/env python3
"""
代理池系统 - 代理调度器模块
管理代理轮换和调度策略
"""

import asyncio
import json
import random
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import heapq

from backend.core.base import BaseScript


class RotationStrategy(Enum):
    """轮换策略枚举"""
    RANDOM = "random"           # 随机选择
    ROUND_ROBIN = "round_robin" # 轮询
    SCORE_BASED = "score_based" # 基于评分
    LEAST_USED = "least_used"   # 最少使用
    FASTEST = "fastest"         # 最快响应


class ProxyStatus(Enum):
    """代理状态枚举"""
    ACTIVE = "active"       # 活跃
    INACTIVE = "inactive"   # 不活跃
    BANNED = "banned"       # 被封禁
    EXPIRED = "expired"     # 过期


@dataclass
class ProxyRecord:
    """代理记录"""
    proxy: Dict[str, Any]
    status: ProxyStatus
    score: float
    use_count: int
    last_used: float
    last_success: float
    last_failure: float
    consecutive_failures: int
    created_at: float
    updated_at: float


class ProxyManager(BaseScript):
    """代理调度器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 代理池
        self.proxy_pool: Dict[str, ProxyRecord] = {}

        # 调度配置
        self.config = {
            'rotation_strategy': RotationStrategy.SCORE_BASED,
            'max_failures': 3,      # 最大连续失败次数
            'ban_duration': 3600,   # 封禁时长(秒)
            'min_score': 30,        # 最小评分阈值
            'max_age': 86400,       # 最大年龄(秒)
            'health_check_interval': 300,  # 健康检查间隔
            'auto_cleanup': True,   # 自动清理
            'geo_filter': None,     # 地理位置过滤
        }

        # 统计信息
        self.stats = {
            'total_proxies': 0,
            'active_proxies': 0,
            'banned_proxies': 0,
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'avg_response_time': 0.0
        }

        # 轮询索引
        self.round_robin_index = 0

        # 响应时间历史
        self.response_times: List[float] = []

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行代理管理操作"""
        try:
            self.logger.info(f"执行代理管理操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'add_proxies':
                result = await self._add_proxies(kwargs.get('proxies', []))
            elif action == 'get_proxy':
                result = await self._get_proxy(kwargs.get('strategy'))
            elif action == 'report_result':
                result = await self._report_result(
                    kwargs.get('proxy_key'),
                    kwargs.get('success'),
                    kwargs.get('response_time', 0)
                )
            elif action == 'health_check':
                result = await self._health_check()
            elif action == 'cleanup':
                result = await self._cleanup()
            elif action == 'get_stats':
                result = self._get_stats()
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

    async def _add_proxies(self, proxies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """添加代理到池中"""
        added_count = 0

        for proxy in proxies:
            proxy_key = self._get_proxy_key(proxy)

            if proxy_key not in self.proxy_pool:
                record = ProxyRecord(
                    proxy=proxy,
                    status=ProxyStatus.ACTIVE,
                    score=proxy.get('score', 50),
                    use_count=0,
                    last_used=0,
                    last_success=time.time(),
                    last_failure=0,
                    consecutive_failures=0,
                    created_at=time.time(),
                    updated_at=time.time()
                )

                self.proxy_pool[proxy_key] = record
                added_count += 1

        self._update_stats()

        return {
            "status": "success",
            "added_count": added_count,
            "total_proxies": len(self.proxy_pool)
        }

    async def _get_proxy(self, strategy: Optional[str] = None) -> Dict[str, Any]:
        """获取一个代理"""
        if not self.proxy_pool:
            return {
                "status": "error",
                "error": "代理池为空"
            }

        # 确定策略
        if strategy:
            try:
                rotation_strategy = RotationStrategy(strategy)
            except ValueError:
                rotation_strategy = self.config['rotation_strategy']
        else:
            rotation_strategy = self.config['rotation_strategy']

        # 获取可用代理
        available_proxies = self._get_available_proxies()

        if not available_proxies:
            return {
                "status": "error",
                "error": "没有可用的代理"
            }

        # 根据策略选择代理
        selected_record = self._select_proxy_by_strategy(available_proxies, rotation_strategy)

        if not selected_record:
            return {
                "status": "error",
                "error": "无法选择代理"
            }

        # 更新使用统计
        selected_record.use_count += 1
        selected_record.last_used = time.time()
        selected_record.updated_at = time.time()

        self.stats['total_requests'] += 1

        return {
            "status": "success",
            "proxy": selected_record.proxy,
            "proxy_key": self._get_proxy_key(selected_record.proxy),
            "strategy": rotation_strategy.value
        }

    def _get_available_proxies(self) -> List[ProxyRecord]:
        """获取可用代理列表"""
        available = []

        for record in self.proxy_pool.values():
            # 检查状态
            if record.status != ProxyStatus.ACTIVE:
                continue

            # 检查评分
            if record.score < self.config['min_score']:
                continue

            # 检查年龄
            age = time.time() - record.created_at
            if age > self.config['max_age']:
                continue

            # 检查地理位置过滤
            if self.config['geo_filter']:
                proxy_country = record.proxy.get('country', '').lower()
                filter_countries = [c.lower() for c in self.config['geo_filter']]
                if proxy_country not in filter_countries:
                    continue

            available.append(record)

        return available

    def _select_proxy_by_strategy(self, available_proxies: List[ProxyRecord],
                                strategy: RotationStrategy) -> Optional[ProxyRecord]:
        """根据策略选择代理"""
        if not available_proxies:
            return None

        if strategy == RotationStrategy.RANDOM:
            return random.choice(available_proxies)

        elif strategy == RotationStrategy.ROUND_ROBIN:
            if self.round_robin_index >= len(available_proxies):
                self.round_robin_index = 0
            selected = available_proxies[self.round_robin_index]
            self.round_robin_index += 1
            return selected

        elif strategy == RotationStrategy.SCORE_BASED:
            # 按评分排序，选择最高评分
            return max(available_proxies, key=lambda x: x.score)

        elif strategy == RotationStrategy.LEAST_USED:
            # 选择使用次数最少的
            return min(available_proxies, key=lambda x: x.use_count)

        elif strategy == RotationStrategy.FASTEST:
            # 选择响应时间最快的（基于历史数据）
            fastest = min(available_proxies,
                         key=lambda x: x.proxy.get('response_time', float('inf')))
            return fastest

        else:
            return random.choice(available_proxies)

    async def _report_result(self, proxy_key: str, success: bool,
                           response_time: float = 0) -> Dict[str, Any]:
        """报告代理使用结果"""
        if proxy_key not in self.proxy_pool:
            return {
                "status": "error",
                "error": f"代理不存在: {proxy_key}"
            }

        record = self.proxy_pool[proxy_key]

        if success:
            record.last_success = time.time()
            record.consecutive_failures = 0
            self.stats['successful_requests'] += 1

            # 更新响应时间
            if response_time > 0:
                self.response_times.append(response_time)
                if len(self.response_times) > 100:  # 保持最近100个记录
                    self.response_times.pop(0)

                # 更新代理的平均响应时间
                record.proxy['response_time'] = response_time

        else:
            record.last_failure = time.time()
            record.consecutive_failures += 1
            self.stats['failed_requests'] += 1

            # 检查是否需要封禁
            if record.consecutive_failures >= self.config['max_failures']:
                record.status = ProxyStatus.BANNED
                self.logger.warning(f"代理 {proxy_key} 被封禁 (连续失败 {record.consecutive_failures} 次)")

        # 更新评分
        record.score = self._calculate_proxy_score(record)
        record.updated_at = time.time()

        self._update_stats()

        return {
            "status": "success",
            "proxy_key": proxy_key,
            "success": success,
            "new_score": record.score
        }

    def _calculate_proxy_score(self, record: ProxyRecord) -> float:
        """计算代理评分"""
        base_score = record.proxy.get('score', 50)

        # 连续失败惩罚
        failure_penalty = record.consecutive_failures * 10

        # 使用频率奖励（避免过度使用）
        usage_bonus = min(record.use_count * 0.1, 10)

        # 时间衰减（较旧的代理评分降低）
        age_hours = (time.time() - record.created_at) / 3600
        age_penalty = age_hours * 0.5

        # 成功率奖励
        total_uses = record.use_count
        if total_uses > 0:
            success_rate = (total_uses - record.consecutive_failures) / total_uses
            success_bonus = (success_rate - 0.5) * 20  # 50%为基准
        else:
            success_bonus = 0

        new_score = base_score - failure_penalty + usage_bonus - age_penalty + success_bonus
        return max(0, min(100, round(new_score, 2)))

    async def _health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        current_time = time.time()
        checked_count = 0
        banned_count = 0

        for proxy_key, record in self.proxy_pool.items():
            # 检查过期代理
            age = current_time - record.created_at
            if age > self.config['max_age']:
                record.status = ProxyStatus.EXPIRED
                checked_count += 1
                continue

            # 检查长时间未使用的代理
            if current_time - record.last_used > 3600:  # 1小时
                record.status = ProxyStatus.INACTIVE

            checked_count += 1

        self._update_stats()

        return {
            "status": "success",
            "checked_count": checked_count,
            "banned_count": banned_count,
            "active_count": self.stats['active_proxies']
        }

    async def _cleanup(self) -> Dict[str, Any]:
        """清理无效代理"""
        if not self.config['auto_cleanup']:
            return {"status": "success", "message": "自动清理已禁用"}

        current_time = time.time()
        removed_count = 0

        # 清理过期代理
        expired_keys = []
        for proxy_key, record in self.proxy_pool.items():
            age = current_time - record.created_at
            if age > self.config['max_age']:
                expired_keys.append(proxy_key)
            elif record.status == ProxyStatus.BANNED:
                ban_age = current_time - record.last_failure
                if ban_age > self.config['ban_duration']:
                    # 解封代理
                    record.status = ProxyStatus.ACTIVE
                    record.consecutive_failures = 0

        # 移除过期代理
        for key in expired_keys:
            del self.proxy_pool[key]
            removed_count += 1

        self._update_stats()

        return {
            "status": "success",
            "removed_count": removed_count,
            "remaining_count": len(self.proxy_pool)
        }

    def _get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        self._update_stats()

        total_requests = self.stats['total_requests']
        success_rate = (self.stats['successful_requests'] / total_requests * 100) if total_requests > 0 else 0

        return {
            "status": "success",
            "stats": {
                **self.stats,
                "success_rate": round(success_rate, 2),
                "avg_response_time": round(sum(self.response_times) / len(self.response_times), 3) if self.response_times else 0
            },
            "pool_size": len(self.proxy_pool),
            "config": self.config
        }

    def _get_proxy_key(self, proxy: Dict[str, Any]) -> str:
        """生成代理唯一键"""
        ip = proxy.get('ip', '')
        port = proxy.get('port', '')
        protocol = proxy.get('protocol', 'http')
        return f"{protocol}://{ip}:{port}"

    def _update_stats(self):
        """更新统计信息"""
        total = len(self.proxy_pool)
        active = len([r for r in self.proxy_pool.values() if r.status == ProxyStatus.ACTIVE])
        banned = len([r for r in self.proxy_pool.values() if r.status == ProxyStatus.BANNED])

        self.stats.update({
            'total_proxies': total,
            'active_proxies': active,
            'banned_proxies': banned
        })

    def set_geo_filter(self, countries: List[str]):
        """设置地理位置过滤"""
        self.config['geo_filter'] = countries

    def set_rotation_strategy(self, strategy: RotationStrategy):
        """设置轮换策略"""
        self.config['rotation_strategy'] = strategy

    async def get_proxy_pool_snapshot(self) -> Dict[str, Any]:
        """获取代理池快照"""
        snapshot = {
            "timestamp": time.time(),
            "total_proxies": len(self.proxy_pool),
            "proxies": []
        }

        for proxy_key, record in self.proxy_pool.items():
            proxy_info = {
                "key": proxy_key,
                "ip": record.proxy.get('ip'),
                "port": record.proxy.get('port'),
                "protocol": record.proxy.get('protocol'),
                "country": record.proxy.get('country'),
                "status": record.status.value,
                "score": record.score,
                "use_count": record.use_count,
                "last_used": record.last_used,
                "consecutive_failures": record.consecutive_failures
            }
            snapshot["proxies"].append(proxy_info)

        return snapshot