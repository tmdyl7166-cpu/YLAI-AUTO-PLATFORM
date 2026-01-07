#!/usr/bin/env python3
"""
AI功能高级配置优化系统
自动优化AI模型配置、参数调优和性能提升
"""

import asyncio
import json
import time
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import aiohttp
from pathlib import Path
import yaml

from backend.core.base import BaseScript
from backend.core.registry import registry
from backend.scripts.ai_coordinator import AIModelCoordinator


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str
    base_url: str
    port: int
    parameters: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    optimization_history: List[Dict[str, Any]]
    last_optimized: float
    status: str  # 'active', 'optimizing', 'error'

    def __post_init__(self):
        if self.parameters is None:
            self.parameters = {}
        if self.performance_metrics is None:
            self.performance_metrics = {}
        if self.optimization_history is None:
            self.optimization_history = []


@dataclass
class OptimizationTask:
    """优化任务"""
    task_id: str
    target_model: str
    optimization_type: str  # 'parameter_tuning', 'config_optimization', 'performance_boost'
    current_config: Dict[str, Any]
    proposed_config: Dict[str, Any]
    expected_improvement: Dict[str, Any]
    status: str  # 'pending', 'running', 'completed', 'failed'
    created_at: float
    completed_at: Optional[float] = None
    results: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@registry.register("ai_optimizer")
class AIOptimizerScript(BaseScript):
    """AI功能高级配置优化系统"""

    name = "ai_optimizer"
    description = "AI功能高级配置优化系统"
    version = "2.0.0"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # AI协调器
        self.ai_coordinator = None

        # 模型配置
        self.model_configs: Dict[str, ModelConfig] = {}

        # 优化任务
        self.optimization_tasks: List[OptimizationTask] = []

        # 配置
        self.config = {
            'optimization_interval': 3600,  # 1小时优化一次
            'benchmark_duration': 300,     # 5分钟基准测试
            'max_concurrent_optimizations': 2,
            'auto_rollback': True,
            'performance_threshold': 0.05,  # 5%性能提升阈值
            'config_backup_path': 'backend/data/ai_config_backups',
        }

        # 默认模型配置
        self.default_configs = {
            'qwen3:8b': {
                'temperature': 0.7,
                'top_p': 0.9,
                'max_tokens': 4096,
                'repetition_penalty': 1.1,
                'context_window': 8192
            },
            'llama3.1:8b': {
                'temperature': 0.8,
                'top_p': 0.95,
                'max_tokens': 4096,
                'repetition_penalty': 1.15,
                'context_window': 8192
            },
            'deepseek-r1:8b': {
                'temperature': 0.6,
                'top_p': 0.85,
                'max_tokens': 8192,
                'repetition_penalty': 1.05,
                'context_window': 16384
            },
            'gpt-oss:20b': {
                'temperature': 0.9,
                'top_p': 0.98,
                'max_tokens': 4096,
                'repetition_penalty': 1.2,
                'context_window': 8192
            }
        }

        # HTTP客户端
        self.session = None

    async def pre_run(self, **kwargs):
        """初始化"""
        await super().pre_run(**kwargs)

        # 初始化HTTP客户端
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30))

        # 初始化AI协调器
        try:
            self.ai_coordinator = AIModelCoordinator()
            await self.ai_coordinator.initialize()
            self.logger.info("✅ AI协调器初始化成功")
        except Exception as e:
            self.logger.warning(f"⚠️ AI协调器初始化失败: {e}")
            self.ai_coordinator = None

        # 初始化模型配置
        await self._initialize_model_configs()

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """
        执行优化操作
        """
        try:
            if action == 'optimize_model':
                result = await self._optimize_model(**kwargs)
            elif action == 'benchmark_models':
                result = await self._benchmark_models(**kwargs)
            elif action == 'auto_tune':
                result = await self._auto_tune(**kwargs)
            elif action == 'performance_analysis':
                result = await self._performance_analysis(**kwargs)
            elif action == 'config_backup':
                result = await self._config_backup(**kwargs)
            else:
                result = {"status": "error", "error": f"未知操作: {action}"}

            return result

        except Exception as e:
            self.logger.error(f"优化操作失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _initialize_model_configs(self):
        """初始化模型配置"""
        for model_name, default_config in self.default_configs.items():
            port_map = {
                'qwen3:8b': 11434,
                'llama3.1:8b': 11435,
                'deepseek-r1:8b': 11436,
                'gpt-oss:20b': 11437
            }

            config = ModelConfig(
                model_name=model_name,
                base_url='http://localhost',
                port=port_map.get(model_name, 11434),
                parameters=default_config.copy(),
                performance_metrics={},
                optimization_history=[],
                status='active'
            )

            self.model_configs[model_name] = config

        self.logger.info(f"✅ 初始化了 {len(self.model_configs)} 个模型配置")

    async def _optimize_model(self, model_name: str, **kwargs) -> Dict[str, Any]:
        """优化单个模型"""
        if model_name not in self.model_configs:
            return {"status": "error", "error": f"模型 {model_name} 不存在"}

        try:
            config = self.model_configs[model_name]

            # 创建优化任务
            task = OptimizationTask(
                task_id=f"opt_{int(time.time())}_{hash(model_name) % 10000}",
                target_model=model_name,
                optimization_type=kwargs.get('optimization_type', 'parameter_tuning'),
                current_config=config.parameters.copy(),
                proposed_config={},
                expected_improvement={}
            )

            self.optimization_tasks.append(task)

            # 执行优化
            result = await self._execute_optimization(task)

            return result

        except Exception as e:
            self.logger.error(f"模型优化失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _execute_optimization(self, task: OptimizationTask) -> Dict[str, Any]:
        """执行优化任务"""
        try:
            task.status = 'running'
            config = self.model_configs[task.target_model]

            # AI生成优化建议
            if self.ai_coordinator:
                optimization_suggestions = await self._ai_generate_optimization_suggestions(task)
                task.proposed_config = optimization_suggestions.get('proposed_config', {})
                task.expected_improvement = optimization_suggestions.get('expected_improvement', {})

            # 应用优化配置
            if task.proposed_config:
                # 备份当前配置
                await self._backup_config(config)

                # 应用新配置
                config.parameters.update(task.proposed_config)
                config.last_optimized = time.time()

                # 基准测试
                benchmark_result = await self._benchmark_model_config(config)

                # 评估优化效果
                improvement = self._evaluate_optimization_improvement(
                    task.current_config, task.proposed_config, benchmark_result
                )

                task.results = {
                    'benchmark_result': benchmark_result,
                    'improvement': improvement,
                    'applied_config': task.proposed_config.copy()
                }

                # 记录优化历史
                config.optimization_history.append({
                    'timestamp': time.time(),
                    'task_id': task.task_id,
                    'type': task.optimization_type,
                    'old_config': task.current_config,
                    'new_config': task.proposed_config,
                    'improvement': improvement,
                    'benchmark': benchmark_result
                })

                # 如果优化效果不佳，回滚配置
                if self.config['auto_rollback'] and improvement.get('overall_score', 0) < 0:
                    await self._rollback_config(config)
                    task.results['rolled_back'] = True

            task.status = 'completed'
            task.completed_at = time.time()

            return {
                "status": "success",
                "task_id": task.task_id,
                "model": task.target_model,
                "optimization_type": task.optimization_type,
                "improvement": task.results.get('improvement', {}),
                "applied": not task.results.get('rolled_back', False)
            }

        except Exception as e:
            task.status = 'failed'
            task.results = {"error": str(e)}
            self.logger.error(f"优化任务执行失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _ai_generate_optimization_suggestions(self, task: OptimizationTask) -> Dict[str, Any]:
        """AI生成优化建议"""
        if not self.ai_coordinator:
            return {}

        try:
            config = self.model_configs[task.target_model]

            optimization_prompt = f"""
            为AI模型生成优化建议：
            模型: {task.target_model}
            当前配置: {json.dumps(task.current_config, ensure_ascii=False, indent=2)}
            优化类型: {task.optimization_type}
            当前性能: {json.dumps(config.performance_metrics, ensure_ascii=False, indent=2)}

            请提供：
            1. 参数优化建议
            2. 预期性能提升
            3. 配置调整理由
            4. 潜在风险评估
            5. 回滚建议
            """

            result = await self.ai_coordinator.run('task_planning', content=optimization_prompt)

            if result.get('status') == 'success':
                suggestions = result.get('result', {})

                # 解析建议
                proposed_config = {}
                expected_improvement = {}

                # 提取配置建议
                if 'parameter_suggestions' in suggestions:
                    for param, value in suggestions['parameter_suggestions'].items():
                        if isinstance(value, (int, float)):
                            proposed_config[param] = value

                # 提取预期改进
                if 'expected_improvements' in suggestions:
                    expected_improvement = suggestions['expected_improvements']

                return {
                    'proposed_config': proposed_config,
                    'expected_improvement': expected_improvement,
                    'reasoning': suggestions.get('reasoning', ''),
                    'risks': suggestions.get('risks', [])
                }

            return {}

        except Exception as e:
            self.logger.error(f"AI优化建议生成失败: {e}")
            return {}

    async def _benchmark_model_config(self, config: ModelConfig) -> Dict[str, Any]:
        """基准测试模型配置"""
        try:
            # 准备测试提示
            test_prompts = [
                "请解释人工智能的发展历程",
                "分析当前科技行业的趋势",
                "描述一个创新的商业模式",
                "解释机器学习的原理"
            ]

            results = []
            total_response_time = 0
            total_tokens = 0

            for prompt in test_prompts:
                try:
                    start_time = time.time()

                    # 发送请求到模型
                    url = f"{config.base_url}:{config.port}/api/generate"
                    payload = {
                        "model": config.model_name,
                        "prompt": prompt,
                        "stream": False,
                        **config.parameters
                    }

                    async with self.session.post(url, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            response_time = time.time() - start_time

                            result = {
                                'prompt': prompt,
                                'response_time': response_time,
                                'success': True,
                                'response_length': len(data.get('response', '')),
                                'tokens_generated': data.get('eval_count', 0)
                            }

                            total_response_time += response_time
                            total_tokens += result['tokens_generated']
                        else:
                            result = {
                                'prompt': prompt,
                                'response_time': time.time() - start_time,
                                'success': False,
                                'error': f"HTTP {response.status}"
                            }

                    results.append(result)

                except Exception as e:
                    results.append({
                        'prompt': prompt,
                        'success': False,
                        'error': str(e)
                    })

            # 计算汇总指标
            successful_requests = sum(1 for r in results if r['success'])
            avg_response_time = total_response_time / len(results) if results else 0
            success_rate = successful_requests / len(results) if results else 0
            avg_tokens_per_second = total_tokens / total_response_time if total_response_time > 0 else 0

            benchmark_result = {
                'total_requests': len(results),
                'successful_requests': successful_requests,
                'success_rate': success_rate,
                'avg_response_time': avg_response_time,
                'avg_tokens_per_second': avg_tokens_per_second,
                'total_tokens': total_tokens,
                'detailed_results': results
            }

            # 更新配置的性能指标
            config.performance_metrics = {
                'last_benchmark': time.time(),
                'avg_response_time': avg_response_time,
                'success_rate': success_rate,
                'tokens_per_second': avg_tokens_per_second
            }

            return benchmark_result

        except Exception as e:
            self.logger.error(f"基准测试失败: {e}")
            return {"error": str(e), "success": False}

    def _evaluate_optimization_improvement(self, old_config: Dict, new_config: Dict,
                                          benchmark_result: Dict) -> Dict[str, Any]:
        """评估优化改进"""
        try:
            improvement = {
                'response_time_improvement': 0.0,
                'success_rate_improvement': 0.0,
                'throughput_improvement': 0.0,
                'overall_score': 0.0
            }

            # 这里应该比较新旧配置的性能差异
            # 由于没有历史基准数据，这里使用简单的评估

            success_rate = benchmark_result.get('success_rate', 0)
            avg_response_time = benchmark_result.get('avg_response_time', 0)

            # 基于当前性能计算分数
            response_time_score = max(0, 1 - avg_response_time / 10)  # 10秒以内得满分
            success_rate_score = success_rate
            throughput_score = benchmark_result.get('avg_tokens_per_second', 0) / 100  # 标准化

            improvement['overall_score'] = (response_time_score + success_rate_score + throughput_score) / 3

            return improvement

        except Exception as e:
            self.logger.error(f"优化改进评估失败: {e}")
            return {'overall_score': 0.0, 'error': str(e)}

    async def _benchmark_models(self, **kwargs) -> Dict[str, Any]:
        """基准测试所有模型"""
        try:
            results = {}

            for model_name, config in self.model_configs.items():
                self.logger.info(f"🔬 基准测试模型: {model_name}")
                benchmark = await self._benchmark_model_config(config)
                results[model_name] = benchmark

            # 生成比较报告
            comparison = await self._generate_benchmark_comparison(results)

            return {
                "status": "success",
                "benchmark_results": results,
                "comparison": comparison
            }

        except Exception as e:
            self.logger.error(f"模型基准测试失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _generate_benchmark_comparison(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """生成基准测试比较报告"""
        if not self.ai_coordinator:
            return {"comparison": "AI未启用，无法生成详细比较"}

        try:
            comparison_prompt = f"""
            分析模型基准测试结果比较：
            测试结果: {json.dumps(results, ensure_ascii=False, indent=2)}

            请提供：
            1. 性能排名
            2. 各模型优缺点
            3. 使用建议
            4. 优化建议
            """

            result = await self.ai_coordinator.run('complex_reasoning', content=comparison_prompt)

            if result.get('status') == 'success':
                return result.get('result', {})
            else:
                return {"comparison": "AI分析失败"}

        except Exception as e:
            self.logger.error(f"基准测试比较生成失败: {e}")
            return {"error": str(e)}

    async def _auto_tune(self, **kwargs) -> Dict[str, Any]:
        """自动调优所有模型"""
        try:
            tuning_results = {}

            for model_name in self.model_configs.keys():
                self.logger.info(f"🎛️ 自动调优模型: {model_name}")

                # 执行优化
                result = await self._optimize_model(
                    model_name,
                    optimization_type='auto_tune'
                )

                tuning_results[model_name] = result

            # 生成调优总结
            summary = await self._generate_tuning_summary(tuning_results)

            return {
                "status": "success",
                "tuning_results": tuning_results,
                "summary": summary
            }

        except Exception as e:
            self.logger.error(f"自动调优失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _generate_tuning_summary(self, tuning_results: Dict[str, Any]) -> Dict[str, Any]:
        """生成调优总结"""
        if not self.ai_coordinator:
            return {"summary": "AI未启用"}

        try:
            summary_prompt = f"""
            分析自动调优结果总结：
            调优结果: {json.dumps(tuning_results, ensure_ascii=False, indent=2)}

            请提供：
            1. 整体优化效果评估
            2. 各模型改进情况
            3. 最佳配置推荐
            4. 后续优化建议
            """

            result = await self.ai_coordinator.run('complex_reasoning', content=summary_prompt)

            if result.get('status') == 'success':
                return result.get('result', {})
            else:
                return {"summary": "AI总结生成失败"}

        except Exception as e:
            self.logger.error(f"调优总结生成失败: {e}")
            return {"error": str(e)}

    async def _performance_analysis(self, **kwargs) -> Dict[str, Any]:
        """性能分析"""
        try:
            analysis = {
                'model_performance': {},
                'optimization_history': {},
                'trends': {},
                'recommendations': []
            }

            # 收集各模型性能数据
            for model_name, config in self.model_configs.items():
                analysis['model_performance'][model_name] = {
                    'current_config': config.parameters,
                    'performance_metrics': config.performance_metrics,
                    'optimization_count': len(config.optimization_history),
                    'last_optimized': config.last_optimized
                }

                analysis['optimization_history'][model_name] = config.optimization_history[-5:]  # 最近5次

            # AI分析性能趋势
            if self.ai_coordinator:
                trends_analysis = await self._ai_analyze_performance_trends(analysis)
                analysis['trends'] = trends_analysis

                # 生成建议
                recommendations = await self._ai_generate_performance_recommendations(analysis)
                analysis['recommendations'] = recommendations

            return {
                "status": "success",
                "performance_analysis": analysis
            }

        except Exception as e:
            self.logger.error(f"性能分析失败: {e}")
            return {"status": "error", "error": str(e)}

    async def _ai_analyze_performance_trends(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """AI分析性能趋势"""
        if not self.ai_coordinator:
            return {}

        try:
            trends_prompt = f"""
            分析AI模型性能趋势：
            性能数据: {json.dumps(analysis, ensure_ascii=False, indent=2)}

            请分析：
            1. 性能变化趋势
            2. 优化效果评估
            3. 瓶颈识别
            4. 未来预测
            """

            result = await self.ai_coordinator.run('complex_reasoning', content=trends_prompt)

            if result.get('status') == 'success':
                return result.get('result', {})
            else:
                return {}

        except Exception as e:
            self.logger.error(f"性能趋势分析失败: {e}")
            return {}

    async def _ai_generate_performance_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """AI生成性能建议"""
        if not self.ai_coordinator:
            return ["启用AI协调器以获得详细建议"]

        try:
            rec_prompt = f"""
            基于性能分析生成优化建议：
            分析数据: {json.dumps(analysis, ensure_ascii=False, indent=2)}

            请提供具体的改进建议列表。
            """

            result = await self.ai_coordinator.run('task_planning', content=rec_prompt)

            if result.get('status') == 'success':
                recommendations = result.get('result', {}).get('recommendations', [])
                return recommendations if isinstance(recommendations, list) else [str(recommendations)]
            else:
                return ["AI建议生成失败"]

        except Exception as e:
            self.logger.error(f"性能建议生成失败: {e}")
            return [f"建议生成异常: {str(e)}"]

    async def _backup_config(self, config: ModelConfig):
        """备份配置"""
        try:
            backup_path = Path(self.config['config_backup_path'])
            backup_path.mkdir(parents=True, exist_ok=True)

            backup_file = backup_path / f"{config.model_name}_{int(time.time())}.json"

            backup_data = {
                'timestamp': time.time(),
                'model_name': config.model_name,
                'parameters': config.parameters.copy(),
                'performance_metrics': config.performance_metrics.copy()
            }

            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)

            self.logger.info(f"✅ 配置备份完成: {backup_file}")

        except Exception as e:
            self.logger.error(f"配置备份失败: {e}")

    async def _rollback_config(self, config: ModelConfig):
        """回滚配置"""
        try:
            backup_path = Path(self.config['config_backup_path'])
            if not backup_path.exists():
                return

            # 找到最新的备份
            backup_files = list(backup_path.glob(f"{config.model_name}_*.json"))
            if not backup_files:
                return

            latest_backup = max(backup_files, key=lambda x: x.stat().st_mtime)

            with open(latest_backup, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)

            # 恢复配置
            config.parameters = backup_data.get('parameters', config.parameters)

            self.logger.info(f"✅ 配置回滚完成: {latest_backup}")

        except Exception as e:
            self.logger.error(f"配置回滚失败: {e}")

    async def _config_backup(self, **kwargs) -> Dict[str, Any]:
        """手动配置备份"""
        try:
            backed_up = []

            for config in self.model_configs.values():
                await self._backup_config(config)
                backed_up.append(config.model_name)

            return {
                "status": "success",
                "backed_up_models": backed_up,
                "backup_path": self.config['config_backup_path']
            }

        except Exception as e:
            self.logger.error(f"配置备份失败: {e}")
            return {"status": "error", "error": str(e)}

    async def post_run(self, result: Dict[str, Any]) -> None:
        """后处理"""
        await super().post_run(result)

        if self.session:
            await self.session.close()

        self.logger.info("⚙️ AI配置优化系统已停止")