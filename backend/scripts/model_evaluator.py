#!/usr/bin/env python3
"""
AI模型评估器
提供全面的模型评估和性能分析功能
"""

import asyncio
import json
import time
import random
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import statistics
try:
    from sklearn.metrics import (
        accuracy_score, precision_score, recall_score, f1_score,
        confusion_matrix, classification_report, roc_auc_score,
        mean_squared_error, mean_absolute_error, r2_score
    )
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("sklearn not available, some evaluation metrics will be disabled")

from backend.core.base import BaseScript
from backend.services.ai_service import AIService


@dataclass
class EvaluationMetric:
    """评估指标"""
    name: str
    value: float
    description: str
    category: str  # 'classification', 'regression', 'general'
    threshold: Optional[float] = None
    status: str = 'unknown'  # 'good', 'warning', 'poor', 'unknown'

    def evaluate_status(self) -> str:
        """评估状态"""
        if self.threshold is None:
            return 'unknown'

        if self.category == 'classification':
            if self.name in ['accuracy', 'precision', 'recall', 'f1_score']:
                if self.value >= self.threshold:
                    return 'good'
                elif self.value >= self.threshold * 0.8:
                    return 'warning'
                else:
                    return 'poor'
        elif self.category == 'regression':
            if self.name in ['r2_score']:
                if self.value >= self.threshold:
                    return 'good'
                elif self.value >= self.threshold * 0.5:
                    return 'warning'
                else:
                    return 'poor'
            elif self.name in ['mse', 'mae']:
                if self.value <= self.threshold:
                    return 'good'
                elif self.value <= self.threshold * 1.5:
                    return 'warning'
                else:
                    return 'poor'

        return 'unknown'


@dataclass
class EvaluationResult:
    """评估结果"""
    model_version: str
    evaluation_id: str
    timestamp: float = None
    metrics: List[EvaluationMetric] = None
    predictions: List[Dict[str, Any]] = None
    test_data_size: int = 0
    evaluation_time: float = 0.0
    overall_score: float = 0.0
    recommendations: List[str] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        if self.recommendations is None:
            self.recommendations = []
        if self.metrics is None:
            self.metrics = []
        if self.predictions is None:
            self.predictions = []


@dataclass
class BenchmarkResult:
    """基准测试结果"""
    benchmark_id: str
    model_version: str
    task_type: str
    latency_ms: float
    throughput: float
    memory_usage_mb: float
    cpu_usage_percent: float
    timestamp: float


class ModelEvaluator(BaseScript):
    """模型评估器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 评估配置
        self.config = {
            'evaluation_dir': 'backend/models/evaluations',
            'benchmark_dir': 'backend/models/benchmarks',
            'test_data_dir': 'backend/data/test',
            'max_evaluations': 100,
            'auto_evaluation_interval': 3600,  # 1小时
            'benchmark_iterations': 100,
            'performance_thresholds': {
                'accuracy': 0.8,
                'precision': 0.75,
                'recall': 0.75,
                'f1_score': 0.8,
                'r2_score': 0.7,
                'mse': 0.1,
                'mae': 0.15,
                'latency_ms': 1000,
                'throughput': 10
            }
        }

        # 评估结果
        self.evaluation_results: Dict[str, EvaluationResult] = {}

        # 基准测试结果
        self.benchmark_results: List[BenchmarkResult] = []

        # AI服务用于模型推理
        self.ai_service = None

        # 统计信息
        self.stats = {
            'total_evaluations': 0,
            'successful_evaluations': 0,
            'failed_evaluations': 0,
            'avg_evaluation_time': 0.0,
            'model_performance_trend': [],
            'best_performing_model': None,
            'evaluation_coverage': 0.0
        }

        # 后台任务
        self.background_tasks = []

        # 创建目录
        self._ensure_directories()

    def _ensure_directories(self):
        """确保目录存在"""
        dirs = [
            self.config['evaluation_dir'],
            self.config['benchmark_dir'],
            self.config['test_data_dir']
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """初始化评估器"""
        await super().initialize()

        # 初始化AI服务
        try:
            self.ai_service = AIService()
            await self.ai_service.initialize()
        except Exception as e:
            self.logger.warning(f"AI服务初始化失败: {e}")

        # 加载评估历史
        await self._load_evaluation_history()

        # 启动后台任务
        await self.start_background_tasks()

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行模型评估操作"""
        try:
            self.logger.info(f"执行模型评估操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'evaluate_model':
                result = await self._evaluate_model(**kwargs)
            elif action == 'benchmark_model':
                result = await self._benchmark_model(**kwargs)
            elif action == 'compare_models':
                result = await self._compare_models(**kwargs)
            elif action == 'generate_report':
                result = await self._generate_report(**kwargs)
            elif action == 'list_evaluations':
                result = await self._list_evaluations(**kwargs)
            elif action == 'get_performance_trend':
                result = await self._get_performance_trend(**kwargs)
            elif action == 'validate_model':
                result = await self._validate_model(**kwargs)
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

    async def _evaluate_model(self, model_version: str, test_data: List[Dict[str, Any]] = None,
                            evaluation_type: str = 'comprehensive', **kwargs) -> Dict[str, Any]:
        """评估模型"""
        try:
            start_time = time.time()

            # 获取测试数据
            if not test_data:
                test_data = await self._load_test_data()

            if not test_data:
                return {"status": "error", "error": "没有可用的测试数据"}

            # 执行推理
            predictions = await self._run_model_inference(model_version, test_data)

            if not predictions:
                return {"status": "error", "error": "模型推理失败"}

            # 计算评估指标
            metrics = await self._calculate_metrics(test_data, predictions, evaluation_type)

            # 生成建议
            recommendations = await self._generate_recommendations(metrics)

            # 计算总体评分
            overall_score = self._calculate_overall_score(metrics)

            # 创建评估结果
            evaluation_id = f"eval_{model_version}_{int(time.time())}"
            evaluation_result = EvaluationResult(
                model_version=model_version,
                evaluation_id=evaluation_id,
                metrics=metrics,
                predictions=predictions,
                test_data_size=len(test_data),
                evaluation_time=time.time() - start_time,
                overall_score=overall_score,
                recommendations=recommendations
            )

            # 保存评估结果
            self.evaluation_results[evaluation_id] = evaluation_result
            await self._save_evaluation_result(evaluation_result)

            # 更新统计信息
            self.stats['total_evaluations'] += 1
            self.stats['successful_evaluations'] += 1
            self.stats['avg_evaluation_time'] = (
                (self.stats['avg_evaluation_time'] * (self.stats['total_evaluations'] - 1) +
                 evaluation_result.evaluation_time) / self.stats['total_evaluations']
            )

            # 更新性能趋势
            self.stats['model_performance_trend'].append({
                'model_version': model_version,
                'timestamp': evaluation_result.timestamp,
                'overall_score': overall_score
            })

            # 更新最佳模型
            if (not self.stats['best_performing_model'] or
                overall_score > self.stats['best_performing_model']['score']):
                self.stats['best_performing_model'] = {
                    'version': model_version,
                    'score': overall_score,
                    'evaluation_id': evaluation_id
                }

            return {
                "status": "success",
                "evaluation_id": evaluation_id,
                "model_version": model_version,
                "overall_score": overall_score,
                "metrics": [asdict(m) for m in metrics],
                "recommendations": recommendations,
                "evaluation_time": evaluation_result.evaluation_time
            }

        except Exception as e:
            self.stats['failed_evaluations'] += 1
            self.logger.error(f"评估模型失败: {e}")
            return {"status": "error", "error": f"评估模型失败: {e}"}

    async def _run_model_inference(self, model_version: str, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """运行模型推理"""
        try:
            predictions = []

            for item in test_data:
                try:
                    # 这里应该调用实际的模型推理
                    # 为了演示，使用模拟推理
                    prediction = await self._mock_model_inference(item)

                    predictions.append({
                        'input': item,
                        'prediction': prediction,
                        'confidence': random.uniform(0.5, 1.0),
                        'inference_time': random.uniform(0.01, 0.1)
                    })

                except Exception as e:
                    self.logger.error(f"推理失败: {e}")
                    predictions.append({
                        'input': item,
                        'prediction': None,
                        'error': str(e),
                        'confidence': 0.0,
                        'inference_time': 0.0
                    })

            return predictions

        except Exception as e:
            self.logger.error(f"模型推理失败: {e}")
            return []

    async def _mock_model_inference(self, input_data: Dict[str, Any]) -> Any:
        """模拟模型推理"""
        # 这里是模拟实现，实际应调用真实的模型
        await asyncio.sleep(0.01)  # 模拟推理时间

        input_text = input_data.get('input_data', '')
        if isinstance(input_text, str):
            # 文本分类模拟
            if 'positive' in input_text.lower():
                return 'positive'
            elif 'negative' in input_text.lower():
                return 'negative'
            else:
                return 'neutral'
        else:
            # 数值预测模拟
            return random.uniform(0, 1)

    async def _calculate_metrics(self, test_data: List[Dict[str, Any]],
                               predictions: List[Dict[str, Any]],
                               evaluation_type: str) -> List[EvaluationMetric]:
        """计算评估指标"""
        try:
            metrics = []

            # 过滤有效的预测
            valid_predictions = [p for p in predictions if p['prediction'] is not None]
            valid_test_data = [test_data[i] for i, p in enumerate(predictions) if p['prediction'] is not None]

            if not valid_predictions:
                return metrics

            # 提取真实值和预测值
            y_true = [item.get('target_output', item.get('label', 0)) for item in valid_test_data]
            y_pred = [p['prediction'] for p in valid_predictions]

            # 判断任务类型
            task_type = self._determine_task_type(y_true, y_pred)

            if task_type == 'classification':
                # 分类指标
                try:
                    accuracy = accuracy_score(y_true, y_pred)
                    metrics.append(EvaluationMetric(
                        name='accuracy',
                        value=accuracy,
                        description='准确率',
                        category='classification',
                        threshold=self.config['performance_thresholds'].get('accuracy', 0.8)
                    ))
                    metrics[-1].status = metrics[-1].evaluate_status()

                    if len(set(y_true)) > 1:
                        precision = precision_score(y_true, y_pred, average='weighted', zero_division=0)
                        metrics.append(EvaluationMetric(
                            name='precision',
                            value=precision,
                            description='精确率',
                            category='classification',
                            threshold=self.config['performance_thresholds'].get('precision', 0.75)
                        ))
                        metrics[-1].status = metrics[-1].evaluate_status()

                        recall = recall_score(y_true, y_pred, average='weighted', zero_division=0)
                        metrics.append(EvaluationMetric(
                            name='recall',
                            value=recall,
                            description='召回率',
                            category='classification',
                            threshold=self.config['performance_thresholds'].get('recall', 0.75)
                        ))
                        metrics[-1].status = metrics[-1].evaluate_status()

                        f1 = f1_score(y_true, y_pred, average='weighted', zero_division=0)
                        metrics.append(EvaluationMetric(
                            name='f1_score',
                            value=f1,
                            description='F1分数',
                            category='classification',
                            threshold=self.config['performance_thresholds'].get('f1_score', 0.8)
                        ))
                        metrics[-1].status = metrics[-1].evaluate_status()

                except Exception as e:
                    self.logger.error(f"计算分类指标失败: {e}")

            elif task_type == 'regression':
                # 回归指标
                try:
                    y_true_numeric = [float(y) for y in y_true]
                    y_pred_numeric = [float(y) for y in y_pred]

                    mse = mean_squared_error(y_true_numeric, y_pred_numeric)
                    metrics.append(EvaluationMetric(
                        name='mse',
                        value=mse,
                        description='均方误差',
                        category='regression',
                        threshold=self.config['performance_thresholds'].get('mse', 0.1)
                    ))
                    metrics[-1].status = metrics[-1].evaluate_status()

                    mae = mean_absolute_error(y_true_numeric, y_pred_numeric)
                    metrics.append(EvaluationMetric(
                        name='mae',
                        value=mae,
                        description='平均绝对误差',
                        category='regression',
                        threshold=self.config['performance_thresholds'].get('mae', 0.15)
                    ))
                    metrics[-1].status = metrics[-1].evaluate_status()

                    r2 = r2_score(y_true_numeric, y_pred_numeric)
                    metrics.append(EvaluationMetric(
                        name='r2_score',
                        value=r2,
                        description='R²决定系数',
                        category='regression',
                        threshold=self.config['performance_thresholds'].get('r2_score', 0.7)
                    ))
                    metrics[-1].status = metrics[-1].evaluate_status()

                except Exception as e:
                    self.logger.error(f"计算回归指标失败: {e}")

            # 通用指标
            inference_times = [p['inference_time'] for p in valid_predictions]
            if inference_times:
                avg_latency = statistics.mean(inference_times) * 1000  # 转换为毫秒
                metrics.append(EvaluationMetric(
                    name='avg_latency_ms',
                    value=avg_latency,
                    description='平均推理延迟(毫秒)',
                    category='general',
                    threshold=self.config['performance_thresholds'].get('latency_ms', 1000)
                ))
                metrics[-1].status = metrics[-1].evaluate_status()

            return metrics

        except Exception as e:
            self.logger.error(f"计算指标失败: {e}")
            return []

    def _determine_task_type(self, y_true: List[Any], y_pred: List[Any]) -> str:
        """判断任务类型"""
        try:
            # 检查是否为分类任务
            if all(isinstance(y, (str, int)) and not isinstance(y, (float, complex)) for y in y_true + y_pred):
                unique_labels = set(str(y) for y in y_true + y_pred)
                if len(unique_labels) <= 20:  # 假设分类任务的类别数不超过20
                    return 'classification'

            # 检查是否为回归任务
            if all(isinstance(y, (int, float)) for y in y_true + y_pred):
                return 'regression'

            return 'unknown'

        except Exception:
            return 'unknown'

    async def _generate_recommendations(self, metrics: List[EvaluationMetric]) -> List[str]:
        """生成建议"""
        recommendations = []

        try:
            poor_metrics = [m for m in metrics if m.status == 'poor']
            warning_metrics = [m for m in metrics if m.status == 'warning']

            for metric in poor_metrics + warning_metrics:
                if metric.name == 'accuracy':
                    recommendations.append("准确率较低，建议增加训练数据或调整模型架构")
                elif metric.name == 'precision':
                    recommendations.append("精确率需要提升，可能存在较多误报")
                elif metric.name == 'recall':
                    recommendations.append("召回率不足，可能存在较多漏报")
                elif metric.name == 'f1_score':
                    recommendations.append("F1分数不理想，建议平衡精确率和召回率")
                elif metric.name == 'mse':
                    recommendations.append("均方误差较大，模型预测偏差较大")
                elif metric.name == 'mae':
                    recommendations.append("平均绝对误差较高，预测准确性需要改进")
                elif metric.name == 'r2_score':
                    recommendations.append("R²分数较低，模型解释能力不足")
                elif metric.name == 'avg_latency_ms':
                    recommendations.append("推理延迟较高，建议优化模型或使用更快的硬件")

            if not poor_metrics and not warning_metrics:
                recommendations.append("模型性能良好，可以考虑部署到生产环境")

            if len(metrics) < 3:
                recommendations.append("评估指标不完整，建议增加更多测试数据")

        except Exception as e:
            self.logger.error(f"生成建议失败: {e}")
            recommendations.append("无法生成具体建议，请检查评估结果")

        return recommendations

    def _calculate_overall_score(self, metrics: List[EvaluationMetric]) -> float:
        """计算总体评分"""
        try:
            if not metrics:
                return 0.0

            # 权重配置
            weights = {
                'accuracy': 0.3,
                'f1_score': 0.3,
                'precision': 0.2,
                'recall': 0.2,
                'r2_score': 0.4,
                'mse': 0.3,
                'mae': 0.3,
                'avg_latency_ms': 0.1
            }

            total_score = 0.0
            total_weight = 0.0

            for metric in metrics:
                weight = weights.get(metric.name, 0.1)
                score = metric.value

                # 归一化延迟指标（越低越好）
                if metric.name == 'avg_latency_ms':
                    threshold = metric.threshold or 1000
                    score = max(0, 1 - (score / threshold))
                elif metric.name in ['mse', 'mae']:
                    # 误差指标归一化（越低越好）
                    threshold = metric.threshold or 1.0
                    score = max(0, 1 - (score / threshold))

                total_score += score * weight
                total_weight += weight

            return total_score / total_weight if total_weight > 0 else 0.0

        except Exception as e:
            self.logger.error(f"计算总体评分失败: {e}")
            return 0.0

    async def _benchmark_model(self, model_version: str, iterations: int = None, **kwargs) -> Dict[str, Any]:
        """基准测试模型"""
        try:
            iterations = iterations or self.config['benchmark_iterations']

            benchmark_id = f"bench_{model_version}_{int(time.time())}"

            # 执行基准测试
            results = []
            for i in range(iterations):
                start_time = time.time()

                # 模拟推理
                await self._mock_model_inference({'input_data': f'test_input_{i}'})

                latency = (time.time() - start_time) * 1000  # 毫秒

                results.append(latency)

            # 计算统计信息
            avg_latency = statistics.mean(results)
            min_latency = min(results)
            max_latency = max(results)
            p95_latency = np.percentile(results, 95)
            throughput = 1000 / avg_latency  # 每秒推理次数

            # 创建基准测试结果
            benchmark_result = BenchmarkResult(
                benchmark_id=benchmark_id,
                model_version=model_version,
                task_type='inference',
                latency_ms=avg_latency,
                throughput=throughput,
                memory_usage_mb=random.uniform(100, 500),  # 模拟内存使用
                cpu_usage_percent=random.uniform(10, 80),  # 模拟CPU使用
                timestamp=time.time()
            )

            self.benchmark_results.append(benchmark_result)
            await self._save_benchmark_result(benchmark_result)

            return {
                "status": "success",
                "benchmark_id": benchmark_id,
                "model_version": model_version,
                "avg_latency_ms": avg_latency,
                "min_latency_ms": min_latency,
                "max_latency_ms": max_latency,
                "p95_latency_ms": p95_latency,
                "throughput": throughput,
                "iterations": iterations
            }

        except Exception as e:
            self.logger.error(f"基准测试失败: {e}")
            return {"status": "error", "error": f"基准测试失败: {e}"}

    async def _compare_models(self, model_versions: List[str], **kwargs) -> Dict[str, Any]:
        """比较模型"""
        try:
            if len(model_versions) < 2:
                return {"status": "error", "error": "至少需要2个模型版本进行比较"}

            comparison_data = []

            for version in model_versions:
                # 获取该版本的最新评估结果
                version_evaluations = [e for e in self.evaluation_results.values() if e.model_version == version]
                if not version_evaluations:
                    continue

                latest_eval = max(version_evaluations, key=lambda x: x.timestamp)

                comparison_data.append({
                    'version': version,
                    'overall_score': latest_eval.overall_score,
                    'metrics': {m.name: m.value for m in latest_eval.metrics},
                    'evaluation_time': latest_eval.evaluation_time,
                    'test_data_size': latest_eval.test_data_size
                })

            if len(comparison_data) < 2:
                return {"status": "error", "error": "没有足够的评估数据进行比较"}

            # 找出最佳模型
            best_model = max(comparison_data, key=lambda x: x['overall_score'])

            return {
                "status": "success",
                "models_compared": len(comparison_data),
                "best_model": best_model['version'],
                "best_score": best_model['overall_score'],
                "comparison_data": comparison_data
            }

        except Exception as e:
            self.logger.error(f"比较模型失败: {e}")
            return {"status": "error", "error": f"比较模型失败: {e}"}

    async def _generate_report(self, evaluation_id: str = None, output_format: str = 'json', **kwargs) -> Dict[str, Any]:
        """生成评估报告"""
        try:
            if evaluation_id:
                if evaluation_id not in self.evaluation_results:
                    return {"status": "error", "error": "评估结果不存在"}

                evaluation = self.evaluation_results[evaluation_id]
                report_data = self._generate_single_report(evaluation)
            else:
                # 生成综合报告
                report_data = await self._generate_comprehensive_report()

            # 保存报告
            timestamp = int(time.time())
            report_path = f"{self.config['evaluation_dir']}/report_{timestamp}.{output_format}"

            with open(report_path, 'w', encoding='utf-8') as f:
                if output_format == 'json':
                    json.dump(report_data, f, ensure_ascii=False, indent=2)
                else:
                    # 简化的文本报告
                    f.write(f"AI模型评估报告\n生成时间: {datetime.fromtimestamp(timestamp)}\n\n")
                    f.write(f"总体评分: {report_data.get('overall_score', 'N/A')}\n")
                    f.write(f"评估数量: {report_data.get('total_evaluations', 0)}\n")
                    f.write(f"最佳模型: {report_data.get('best_model', 'N/A')}\n")

            return {
                "status": "success",
                "report_path": report_path,
                "report_data": report_data
            }

        except Exception as e:
            self.logger.error(f"生成报告失败: {e}")
            return {"status": "error", "error": f"生成报告失败: {e}"}

    def _generate_single_report(self, evaluation: EvaluationResult) -> Dict[str, Any]:
        """生成单个评估报告"""
        return {
            'evaluation_id': evaluation.evaluation_id,
            'model_version': evaluation.model_version,
            'timestamp': evaluation.timestamp,
            'overall_score': evaluation.overall_score,
            'metrics': [asdict(m) for m in evaluation.metrics],
            'recommendations': evaluation.recommendations,
            'test_data_size': evaluation.test_data_size,
            'evaluation_time': evaluation.evaluation_time
        }

    async def _generate_comprehensive_report(self) -> Dict[str, Any]:
        """生成综合报告"""
        try:
            total_evaluations = len(self.evaluation_results)
            if total_evaluations == 0:
                return {"message": "没有评估数据"}

            # 计算统计信息
            scores = [e.overall_score for e in self.evaluation_results.values()]
            avg_score = statistics.mean(scores) if scores else 0
            best_score = max(scores) if scores else 0
            worst_score = min(scores) if scores else 0

            # 模型版本统计
            version_stats = {}
            for evaluation in self.evaluation_results.values():
                version = evaluation.model_version
                if version not in version_stats:
                    version_stats[version] = {'count': 0, 'avg_score': 0, 'scores': []}
                version_stats[version]['count'] += 1
                version_stats[version]['scores'].append(evaluation.overall_score)

            for stats in version_stats.values():
                stats['avg_score'] = statistics.mean(stats['scores']) if stats['scores'] else 0
                del stats['scores']

            # 找出最佳模型
            best_model = max(version_stats.items(), key=lambda x: x[1]['avg_score'])[0] if version_stats else None

            return {
                'total_evaluations': total_evaluations,
                'avg_score': avg_score,
                'best_score': best_score,
                'worst_score': worst_score,
                'best_model': best_model,
                'model_version_stats': version_stats,
                'performance_trend': self.stats['model_performance_trend'][-10:],  # 最近10次评估
                'generated_at': time.time()
            }

        except Exception as e:
            self.logger.error(f"生成综合报告失败: {e}")
            return {"error": f"生成综合报告失败: {e}"}

    async def _list_evaluations(self, model_version: str = None, limit: int = 50, **kwargs) -> Dict[str, Any]:
        """列出评估结果"""
        try:
            evaluations = list(self.evaluation_results.values())

            if model_version:
                evaluations = [e for e in evaluations if e.model_version == model_version]

            # 按时间排序
            evaluations.sort(key=lambda x: x.timestamp, reverse=True)

            evaluations_data = [asdict(e) for e in evaluations[:limit]]

            return {
                "status": "success",
                "total_evaluations": len(self.evaluation_results),
                "filtered_evaluations": len(evaluations),
                "evaluations": evaluations_data
            }

        except Exception as e:
            self.logger.error(f"列出评估失败: {e}")
            return {"status": "error", "error": f"列出评估失败: {e}"}

    async def _get_performance_trend(self, model_version: str = None, **kwargs) -> Dict[str, Any]:
        """获取性能趋势"""
        try:
            trend_data = self.stats['model_performance_trend']

            if model_version:
                trend_data = [t for t in trend_data if t['model_version'] == model_version]

            # 按时间排序
            trend_data.sort(key=lambda x: x['timestamp'])

            return {
                "status": "success",
                "trend_data": trend_data,
                "total_points": len(trend_data)
            }

        except Exception as e:
            self.logger.error(f"获取性能趋势失败: {e}")
            return {"status": "error", "error": f"获取性能趋势失败: {e}"}

    async def _validate_model(self, model_version: str, validation_data: List[Dict[str, Any]] = None, **kwargs) -> Dict[str, Any]:
        """验证模型"""
        try:
            if not validation_data:
                validation_data = await self._load_validation_data()

            if not validation_data:
                return {"status": "error", "error": "没有验证数据"}

            # 执行快速验证
            validation_result = await self._evaluate_model(
                model_version=model_version,
                test_data=validation_data,
                evaluation_type='quick'
            )

            if validation_result['status'] == 'success':
                # 检查是否通过验证
                overall_score = validation_result['overall_score']
                threshold = 0.7  # 验证阈值

                validation_status = 'passed' if overall_score >= threshold else 'failed'

                return {
                    "status": "success",
                    "validation_status": validation_status,
                    "model_version": model_version,
                    "overall_score": overall_score,
                    "threshold": threshold,
                    "details": validation_result
                }
            else:
                return {
                    "status": "error",
                    "validation_status": "error",
                    "error": validation_result.get('error', '验证失败')
                }

        except Exception as e:
            self.logger.error(f"验证模型失败: {e}")
            return {"status": "error", "error": f"验证模型失败: {e}"}

    async def _load_test_data(self) -> List[Dict[str, Any]]:
        """加载测试数据"""
        try:
            test_file = Path(self.config['test_data_dir']) / 'test_data.json'
            if test_file.exists():
                with open(test_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 生成模拟测试数据
                return self._generate_mock_test_data()
        except Exception as e:
            self.logger.error(f"加载测试数据失败: {e}")
            return []

    async def _load_validation_data(self) -> List[Dict[str, Any]]:
        """加载验证数据"""
        try:
            validation_file = Path(self.config['test_data_dir']) / 'validation_data.json'
            if validation_file.exists():
                with open(validation_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # 使用测试数据作为验证数据
                return await self._load_test_data()
        except Exception as e:
            self.logger.error(f"加载验证数据失败: {e}")
            return []

    def _generate_mock_test_data(self) -> List[Dict[str, Any]]:
        """生成模拟测试数据"""
        test_data = []
        for i in range(100):
            if i % 3 == 0:
                label = 'positive'
                text = f"This is a positive example {i} with good content"
            elif i % 3 == 1:
                label = 'negative'
                text = f"This is a negative example {i} with bad content"
            else:
                label = 'neutral'
                text = f"This is a neutral example {i} with regular content"

            test_data.append({
                'id': f'test_{i}',
                'input_data': text,
                'target_output': label,
                'sample_type': 'text'
            })

        return test_data

    async def _save_evaluation_result(self, evaluation: EvaluationResult):
        """保存评估结果"""
        try:
            result_file = Path(self.config['evaluation_dir']) / f"{evaluation.evaluation_id}.json"

            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(evaluation), f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"保存评估结果失败: {e}")

    async def _save_benchmark_result(self, benchmark: BenchmarkResult):
        """保存基准测试结果"""
        try:
            result_file = Path(self.config['benchmark_dir']) / f"{benchmark.benchmark_id}.json"

            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(benchmark), f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"保存基准测试结果失败: {e}")

    async def _load_evaluation_history(self):
        """加载评估历史"""
        try:
            evaluation_dir = Path(self.config['evaluation_dir'])
            if evaluation_dir.exists():
                for file_path in evaluation_dir.glob('eval_*.json'):
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            evaluation = EvaluationResult(**data)
                            self.evaluation_results[evaluation.evaluation_id] = evaluation
                    except Exception as e:
                        self.logger.error(f"加载评估结果失败 {file_path}: {e}")

        except Exception as e:
            self.logger.error(f"加载评估历史失败: {e}")

    async def start_background_tasks(self):
        """启动后台任务"""
        # 自动评估任务
        auto_eval_task = asyncio.create_task(self._background_evaluation())
        self.background_tasks.append(auto_eval_task)

        # 性能监控任务
        performance_task = asyncio.create_task(self._background_performance_monitoring())
        self.background_tasks.append(performance_task)

    async def _background_evaluation(self):
        """后台自动评估"""
        while True:
            try:
                await asyncio.sleep(self.config['auto_evaluation_interval'])

                # 获取最新的模型版本
                # 这里需要与模型训练器集成获取最新版本
                # 暂时跳过

            except Exception as e:
                self.logger.error(f"后台评估出错: {e}")
                await asyncio.sleep(300)

    async def _background_performance_monitoring(self):
        """后台性能监控"""
        while True:
            try:
                await asyncio.sleep(1800)  # 30分钟监控一次

                # 计算评估覆盖率
                total_models = len(set(e.model_version for e in self.evaluation_results.values()))
                evaluated_models = len(self.evaluation_results)

                if total_models > 0:
                    self.stats['evaluation_coverage'] = evaluated_models / total_models

            except Exception as e:
                self.logger.error(f"后台性能监控出错: {e}")
                await asyncio.sleep(300)