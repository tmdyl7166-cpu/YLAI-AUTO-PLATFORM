#!/usr/bin/env python3
"""
策略切换系统 - 动态策略管理模块
根据风控检测结果动态调整采集策略
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from backend.core.base import BaseScript


class StrategyType(Enum):
    """策略类型枚举"""
    NORMAL = "normal"           # 正常采集
    STEALTH = "stealth"         # 隐身模式
    AGGRESSIVE = "aggressive"   # 激进模式
    ROTATION = "rotation"       # 轮换模式
    BACKOFF = "backoff"         # 退避模式


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class StrategyConfig:
    """策略配置"""
    type: StrategyType
    risk_level: RiskLevel
    proxy_rotation: bool = False
    user_agent_rotation: bool = True
    delay_range: tuple = (1, 3)
    max_concurrent: int = 5
    timeout: int = 30
    retry_count: int = 3
    javascript_enabled: bool = False
    headless: bool = True
    session_persistence: bool = False


class StrategySwitcher(BaseScript):
    """策略切换器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 策略配置库
        self.strategy_configs = {
            StrategyType.NORMAL: StrategyConfig(
                type=StrategyType.NORMAL,
                risk_level=RiskLevel.LOW,
                proxy_rotation=False,
                delay_range=(1, 3),
                max_concurrent=10,
                javascript_enabled=False
            ),
            StrategyType.STEALTH: StrategyConfig(
                type=StrategyType.STEALTH,
                risk_level=RiskLevel.MEDIUM,
                proxy_rotation=True,
                delay_range=(3, 8),
                max_concurrent=3,
                javascript_enabled=True,
                session_persistence=True
            ),
            StrategyType.AGGRESSIVE: StrategyConfig(
                type=StrategyType.AGGRESSIVE,
                risk_level=RiskLevel.HIGH,
                proxy_rotation=True,
                user_agent_rotation=True,
                delay_range=(0.5, 2),
                max_concurrent=20,
                retry_count=5
            ),
            StrategyType.ROTATION: StrategyConfig(
                type=StrategyType.ROTATION,
                risk_level=RiskLevel.MEDIUM,
                proxy_rotation=True,
                delay_range=(2, 5),
                max_concurrent=5,
                session_persistence=False
            ),
            StrategyType.BACKOFF: StrategyConfig(
                type=StrategyType.BACKOFF,
                risk_level=RiskLevel.CRITICAL,
                proxy_rotation=True,
                delay_range=(10, 30),
                max_concurrent=1,
                retry_count=1,
                javascript_enabled=True
            )
        }

        # 当前策略状态
        self.current_strategy = StrategyType.NORMAL
        self.strategy_history = []
        self.risk_thresholds = {
            RiskLevel.LOW: 0.3,
            RiskLevel.MEDIUM: 0.6,
            RiskLevel.HIGH: 0.8,
            RiskLevel.CRITICAL: 0.95
        }

        # 策略切换规则
        self.switch_rules = {
            'waf_cloudflare': StrategyType.STEALTH,
            'waf_aliyun': StrategyType.STEALTH,
            'captcha_recaptcha': StrategyType.STEALTH,
            'captcha_hcaptcha': StrategyType.STEALTH,
            'rate_limit': StrategyType.BACKOFF,
            'ip_block': StrategyType.ROTATION,
            'javascript_required': StrategyType.STEALTH,
            'bot_detection': StrategyType.STEALTH
        }

    async def run(self, risk_analysis: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行策略切换"""
        try:
            self.logger.info("开始策略切换分析")

            # 预运行检查
            await self.pre_run()

            # 分析并切换策略
            result = await self._analyze_and_switch(risk_analysis, **kwargs)

            # 后运行处理
            await self.post_run(result)

            return result

        except Exception as e:
            await self.on_error(e)
            return {
                "status": "error",
                "error": str(e),
                "current_strategy": self.current_strategy.value
            }

    async def _analyze_and_switch(self, risk_analysis: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """分析风险并切换策略"""
        risk_types = risk_analysis.get('risk_types', [])
        confidence_scores = risk_analysis.get('confidence_scores', {})

        # 计算整体风险等级
        overall_risk_level = self._calculate_overall_risk_level(risk_types, confidence_scores)

        # 确定推荐策略
        recommended_strategy = self._determine_recommended_strategy(risk_types, overall_risk_level)

        # 检查是否需要切换策略
        should_switch = self._should_switch_strategy(recommended_strategy, risk_analysis)

        result = {
            "current_strategy": self.current_strategy.value,
            "recommended_strategy": recommended_strategy.value,
            "overall_risk_level": overall_risk_level.value,
            "should_switch": should_switch,
            "risk_types": risk_types,
            "confidence_scores": confidence_scores,
            "strategy_config": self._get_strategy_config_dict(recommended_strategy),
            "timestamp": time.time(),
            "status": "success"
        }

        if should_switch:
            # 执行策略切换
            await self._switch_strategy(recommended_strategy)
            result["switched_to"] = recommended_strategy.value
            result["switch_reason"] = self._get_switch_reason(risk_types, confidence_scores)

        # 记录策略历史
        self._record_strategy_history(result)

        return result

    def _calculate_overall_risk_level(self, risk_types: List[str],
                                    confidence_scores: Dict[str, float]) -> RiskLevel:
        """计算整体风险等级"""
        if not risk_types:
            return RiskLevel.LOW

        # 计算加权风险分数
        total_score = 0.0
        weights = {
            'waf': 0.8,
            'captcha': 0.9,
            'ip_block': 1.0,
            'rate_limit': 0.7,
            'bot_detection': 0.8,
            'javascript_required': 0.6,
            'user_agent_check': 0.5
        }

        for risk_type in risk_types:
            confidence = confidence_scores.get(risk_type, 0.0)
            weight = 0.5  # 默认权重

            # 根据风险类型调整权重
            for category, category_weight in weights.items():
                if category in risk_type:
                    weight = category_weight
                    break

            total_score += confidence * weight

        # 归一化到0-1范围
        avg_score = min(1.0, total_score / len(risk_types))

        # 根据分数确定风险等级
        if avg_score >= self.risk_thresholds[RiskLevel.CRITICAL]:
            return RiskLevel.CRITICAL
        elif avg_score >= self.risk_thresholds[RiskLevel.HIGH]:
            return RiskLevel.HIGH
        elif avg_score >= self.risk_thresholds[RiskLevel.MEDIUM]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _determine_recommended_strategy(self, risk_types: List[str],
                                      overall_risk_level: RiskLevel) -> StrategyType:
        """确定推荐策略"""
        # 基于具体风险类型推荐策略
        for risk_type in risk_types:
            if risk_type in self.switch_rules:
                return self.switch_rules[risk_type]

        # 基于整体风险等级推荐策略
        risk_strategy_map = {
            RiskLevel.LOW: StrategyType.NORMAL,
            RiskLevel.MEDIUM: StrategyType.STEALTH,
            RiskLevel.HIGH: StrategyType.ROTATION,
            RiskLevel.CRITICAL: StrategyType.BACKOFF
        }

        return risk_strategy_map.get(overall_risk_level, StrategyType.STEALTH)

    def _should_switch_strategy(self, recommended_strategy: StrategyType,
                               risk_analysis: Dict[str, Any]) -> bool:
        """判断是否需要切换策略"""
        # 如果推荐策略与当前策略相同，不切换
        if recommended_strategy == self.current_strategy:
            return False

        # 检查风险检测结果
        risk_detected = risk_analysis.get('risk_detected', False)
        if not risk_detected:
            # 没有检测到风险，可以保持当前策略或回到正常模式
            return recommended_strategy == StrategyType.NORMAL

        # 检查置信度
        confidence_scores = risk_analysis.get('confidence_scores', {})
        max_confidence = max(confidence_scores.values()) if confidence_scores else 0.0

        # 只有当置信度足够高时才切换策略
        return max_confidence >= 0.4

    async def _switch_strategy(self, new_strategy: StrategyType):
        """执行策略切换"""
        old_strategy = self.current_strategy
        self.current_strategy = new_strategy

        self.logger.info(f"策略切换: {old_strategy.value} -> {new_strategy.value}")

        # 这里可以添加策略切换时的额外逻辑
        # 比如通知其他组件、更新配置等

    def _get_strategy_config_dict(self, strategy: StrategyType) -> Dict[str, Any]:
        """获取策略配置字典"""
        config = self.strategy_configs[strategy]
        return {
            "type": config.type.value,
            "risk_level": config.risk_level.value,
            "proxy_rotation": config.proxy_rotation,
            "user_agent_rotation": config.user_agent_rotation,
            "delay_range": config.delay_range,
            "max_concurrent": config.max_concurrent,
            "timeout": config.timeout,
            "retry_count": config.retry_count,
            "javascript_enabled": config.javascript_enabled,
            "headless": config.headless,
            "session_persistence": config.session_persistence
        }

    def _get_switch_reason(self, risk_types: List[str],
                          confidence_scores: Dict[str, float]) -> str:
        """获取切换原因"""
        if not risk_types:
            return "无风险检测，回到正常模式"

        # 找到置信度最高的几个风险类型
        sorted_risks = sorted(confidence_scores.items(), key=lambda x: x[1], reverse=True)
        top_risks = [risk for risk, score in sorted_risks[:3] if score >= 0.4]

        if top_risks:
            return f"检测到高风险类型: {', '.join(top_risks)}"
        else:
            return f"检测到风险类型: {', '.join(risk_types[:3])}"

    def _record_strategy_history(self, result: Dict[str, Any]):
        """记录策略历史"""
        history_entry = {
            "timestamp": result["timestamp"],
            "current_strategy": result["current_strategy"],
            "recommended_strategy": result["recommended_strategy"],
            "overall_risk_level": result["overall_risk_level"],
            "should_switch": result["should_switch"],
            "switched_to": result.get("switched_to"),
            "switch_reason": result.get("switch_reason"),
            "risk_types": result["risk_types"]
        }

        self.strategy_history.append(history_entry)

        # 保持历史记录在合理范围内
        if len(self.strategy_history) > 100:
            self.strategy_history = self.strategy_history[-100:]

    def get_current_strategy_config(self) -> Dict[str, Any]:
        """获取当前策略配置"""
        return self._get_strategy_config_dict(self.current_strategy)

    def get_strategy_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取策略历史记录"""
        return self.strategy_history[-limit:]

    def force_switch_strategy(self, strategy: StrategyType):
        """强制切换策略"""
        self.current_strategy = strategy
        self.logger.info(f"强制切换策略到: {strategy.value}")

    async def adaptive_switch(self, risk_analysis: Dict[str, Any],
                            performance_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """自适应策略切换（考虑性能指标）"""
        # 基于性能指标调整策略
        success_rate = performance_metrics.get('success_rate', 1.0)
        avg_response_time = performance_metrics.get('avg_response_time', 0)

        # 如果成功率很低，即使风险不高也可能需要调整策略
        if success_rate < 0.5:
            return await self.run(risk_analysis)

        # 如果响应时间过长，可能需要更激进的策略
        if avg_response_time > 10 and self.current_strategy == StrategyType.BACKOFF:
            # 可以考虑切换到更快的策略
            pass

        return await self.run(risk_analysis)