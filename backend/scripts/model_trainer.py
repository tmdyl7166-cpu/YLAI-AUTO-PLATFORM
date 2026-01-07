#!/usr/bin/env python3
"""
AI模型训练框架
提供增量学习、样本收集和模型评估功能
"""

import asyncio
import json
import time
import threading
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import pickle

from backend.core.base import BaseScript


@dataclass
class TrainingSample:
    """训练样本"""
    id: str
    input_data: Any
    target_output: Any
    sample_type: str  # 'text', 'image', 'tabular'
    quality_score: float
    source: str
    timestamp: float = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.timestamp is None:
            self.timestamp = time.time()


@dataclass
class ModelVersion:
    """模型版本"""
    version: str
    model_type: str
    training_data_size: int
    performance_metrics: Dict[str, float]
    training_time: float
    created_at: float
    status: str  # 'active', 'deprecated', 'experimental'
    checkpoint_path: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class TrainingConfig:
    """训练配置"""
    model_type: str
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 10
    validation_split: float = 0.2
    early_stopping_patience: int = 5
    save_checkpoints: bool = True
    incremental_learning: bool = True
    data_augmentation: bool = False
    hyperparameter_tuning: bool = False


class ModelTrainer(BaseScript):
    """模型训练器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 训练配置
        self.config = {
            'model_dir': 'backend/models',
            'data_dir': 'backend/data/training',
            'checkpoint_dir': 'backend/models/checkpoints',
            'max_samples': 10000,
            'min_samples_for_training': 100,
            'auto_training_interval': 3600,  # 1小时
            'validation_split': 0.2,
            'test_split': 0.1,
            'sample_quality_threshold': 0.7,
            'model_retention_count': 5,  # 保留最新5个版本
        }

        # 数据管理
        self.samples: List[TrainingSample] = []
        self.model_versions: Dict[str, ModelVersion] = {}

        # 训练状态
        self.training_active = False
        self.current_training = None

        # 统计信息
        self.stats = {
            'total_samples': 0,
            'training_sessions': 0,
            'successful_trainings': 0,
            'failed_trainings': 0,
            'avg_training_time': 0.0,
            'model_improvements': 0,
            'data_quality_score': 0.0
        }

        # 后台任务
        self.background_tasks = []

        # 创建目录
        self._ensure_directories()

    def _ensure_directories(self):
        """确保目录存在"""
        dirs = [
            self.config['model_dir'],
            self.config['data_dir'],
            self.config['checkpoint_dir']
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行模型训练操作"""
        try:
            self.logger.info(f"执行模型训练操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'add_sample':
                result = await self._add_sample(**kwargs)
            elif action == 'train_model':
                result = await self._train_model(**kwargs)
            elif action == 'evaluate_model':
                result = await self._evaluate_model(**kwargs)
            elif action == 'list_samples':
                result = await self._list_samples(**kwargs)
            elif action == 'get_model_info':
                result = await self._get_model_info(**kwargs)
            elif action == 'export_model':
                result = await self._export_model(**kwargs)
            elif action == 'cleanup_old_models':
                result = await self._cleanup_old_models()
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

    async def _add_sample(self, input_data: Any, target_output: Any,
                         sample_type: str = 'text', quality_score: float = 1.0,
                         source: str = 'manual', metadata: Dict[str, Any] = None,
                         **kwargs) -> Dict[str, Any]:
        """添加训练样本"""
        try:
            # 质量检查
            if quality_score < self.config['sample_quality_threshold']:
                return {
                    "status": "rejected",
                    "reason": f"样本质量分数过低: {quality_score} < {self.config['sample_quality_threshold']}"
                }

            # 创建样本
            sample_id = f"sample_{int(time.time())}_{len(self.samples)}"
            sample = TrainingSample(
                id=sample_id,
                input_data=input_data,
                target_output=target_output,
                sample_type=sample_type,
                quality_score=quality_score,
                source=source,
                metadata=metadata or {}
            )

            # 添加到样本集
            self.samples.append(sample)
            self.stats['total_samples'] += 1

            # 限制样本数量
            if len(self.samples) > self.config['max_samples']:
                # 移除最旧的低质量样本
                self.samples.sort(key=lambda x: (x.quality_score, x.timestamp), reverse=True)
                self.samples = self.samples[:self.config['max_samples']]

            # 保存样本到文件
            await self._save_samples()

            # 检查是否可以开始训练
            if (len(self.samples) >= self.config['min_samples_for_training'] and
                not self.training_active):
                # 触发自动训练
                asyncio.create_task(self._auto_train())

            return {
                "status": "success",
                "sample_id": sample_id,
                "total_samples": len(self.samples),
                "can_train": len(self.samples) >= self.config['min_samples_for_training']
            }

        except Exception as e:
            self.logger.error(f"添加样本失败: {e}")
            return {"status": "error", "error": f"添加样本失败: {e}"}

    async def _train_model(self, model_type: str = 'text_classifier',
                         epochs: int = 10, **kwargs) -> Dict[str, Any]:
        """训练模型"""
        try:
            if self.training_active:
                return {"status": "error", "error": "已有训练任务正在进行"}

            if len(self.samples) < self.config['min_samples_for_training']:
                return {
                    "status": "error",
                    "error": f"样本数量不足: {len(self.samples)} < {self.config['min_samples_for_training']}"
                }

            self.training_active = True
            self.current_training = {
                'model_type': model_type,
                'start_time': time.time(),
                'epochs': epochs,
                'status': 'running'
            }

            try:
                # 执行训练
                result = await self._perform_training(model_type, epochs, **kwargs)

                self.stats['training_sessions'] += 1
                if result['status'] == 'success':
                    self.stats['successful_trainings'] += 1

                    # 创建模型版本
                    version = await self._create_model_version(result)

                    # 检查性能提升
                    if await self._check_performance_improvement(version):
                        self.stats['model_improvements'] += 1

                return result

            finally:
                self.training_active = False
                self.current_training = None

        except Exception as e:
            self.training_active = False
            self.current_training = None
            self.stats['failed_trainings'] += 1
            self.logger.error(f"训练模型失败: {e}")
            return {"status": "error", "error": f"训练模型失败: {e}"}

    async def _perform_training(self, model_type: str, epochs: int, **kwargs) -> Dict[str, Any]:
        """执行训练过程"""
        try:
            # 准备数据
            train_data, val_data, test_data = await self._prepare_training_data()

            # 训练配置
            config = TrainingConfig(
                model_type=model_type,
                epochs=epochs,
                batch_size=kwargs.get('batch_size', 32),
                learning_rate=kwargs.get('learning_rate', 0.001)
            )

            # 模拟训练过程（实际实现应调用具体的ML框架）
            training_result = await self._mock_training_process(config, train_data, val_data)

            # 评估模型
            evaluation_result = await self._evaluate_training_result(training_result, test_data)

            return {
                "status": "success",
                "model_type": model_type,
                "epochs": epochs,
                "training_time": training_result.get('training_time', 0),
                "performance": evaluation_result,
                "config": asdict(config)
            }

        except Exception as e:
            self.logger.error(f"执行训练失败: {e}")
            return {"status": "error", "error": f"执行训练失败: {e}"}

    async def _mock_training_process(self, config: TrainingConfig,
                                   train_data: Any, val_data: Any) -> Dict[str, Any]:
        """模拟训练过程"""
        # 这里是模拟实现，实际应使用TensorFlow、PyTorch等框架
        await asyncio.sleep(1)  # 模拟训练时间

        return {
            "training_time": config.epochs * 0.1,  # 模拟时间
            "final_loss": 0.1 + np.random.random() * 0.1,
            "best_epoch": config.epochs // 2,
            "model_path": f"{self.config['model_dir']}/model_{int(time.time())}.pkl"
        }

    async def _evaluate_training_result(self, training_result: Dict[str, Any],
                                      test_data: Any) -> Dict[str, float]:
        """评估训练结果"""
        # 模拟评估指标
        return {
            "accuracy": 0.85 + np.random.random() * 0.1,
            "precision": 0.82 + np.random.random() * 0.1,
            "recall": 0.83 + np.random.random() * 0.1,
            "f1_score": 0.84 + np.random.random() * 0.1,
            "loss": training_result.get('final_loss', 0.2)
        }

    async def _create_model_version(self, training_result: Dict[str, Any]) -> ModelVersion:
        """创建模型版本"""
        version_num = len(self.model_versions) + 1
        version = ModelVersion(
            version=f"v{version_num}",
            model_type=training_result['model_type'],
            training_data_size=len(self.samples),
            performance_metrics=training_result['performance'],
            training_time=training_result['training_time'],
            status='active',
            checkpoint_path=training_result.get('model_path')
        )

        self.model_versions[version.version] = version

        # 保存模型版本信息
        await self._save_model_versions()

        return version

    async def _check_performance_improvement(self, new_version: ModelVersion) -> bool:
        """检查性能提升"""
        if len(self.model_versions) <= 1:
            return True  # 第一个模型算作提升

        # 获取上一个活跃版本
        active_versions = [v for v in self.model_versions.values() if v.status == 'active']
        if not active_versions:
            return True

        prev_version = max(active_versions, key=lambda x: x.created_at)

        # 比较主要指标（这里使用accuracy作为示例）
        new_acc = new_version.performance_metrics.get('accuracy', 0)
        prev_acc = prev_version.performance_metrics.get('accuracy', 0)

        return new_acc > prev_acc

    async def _evaluate_model(self, model_version: str = None, **kwargs) -> Dict[str, Any]:
        """评估模型"""
        try:
            version = model_version or self._get_latest_version()
            if not version or version not in self.model_versions:
                return {"status": "error", "error": "模型版本不存在"}

            model_info = self.model_versions[version]

            # 模拟评估过程
            evaluation = {
                "version": version,
                "metrics": model_info.performance_metrics,
                "evaluation_time": time.time(),
                "test_samples": int(len(self.samples) * self.config['test_split'])
            }

            return {
                "status": "success",
                "evaluation": evaluation
            }

        except Exception as e:
            self.logger.error(f"评估模型失败: {e}")
            return {"status": "error", "error": f"评估模型失败: {e}"}

    async def _list_samples(self, sample_type: str = None, limit: int = 100,
                          **kwargs) -> Dict[str, Any]:
        """列出样本"""
        try:
            filtered_samples = self.samples

            if sample_type:
                filtered_samples = [s for s in filtered_samples if s.sample_type == sample_type]

            # 转换为字典格式
            samples_data = [asdict(s) for s in filtered_samples[-limit:]]

            return {
                "status": "success",
                "total_samples": len(self.samples),
                "filtered_samples": len(filtered_samples),
                "samples": samples_data
            }

        except Exception as e:
            self.logger.error(f"列出样本失败: {e}")
            return {"status": "error", "error": f"列出样本失败: {e}"}

    async def _get_model_info(self, model_version: str = None, **kwargs) -> Dict[str, Any]:
        """获取模型信息"""
        try:
            version = model_version or self._get_latest_version()
            if not version or version not in self.model_versions:
                return {"status": "error", "error": "模型版本不存在"}

            model_info = self.model_versions[version]

            return {
                "status": "success",
                "model_info": asdict(model_info)
            }

        except Exception as e:
            self.logger.error(f"获取模型信息失败: {e}")
            return {"status": "error", "error": f"获取模型信息失败: {e}"}

    async def _export_model(self, model_version: str = None, export_path: str = None,
                          **kwargs) -> Dict[str, Any]:
        """导出模型"""
        try:
            version = model_version or self._get_latest_version()
            if not version or version not in self.model_versions:
                return {"status": "error", "error": "模型版本不存在"}

            model_info = self.model_versions[version]

            export_path = export_path or f"{self.config['model_dir']}/export_{version}_{int(time.time())}.pkl"

            # 模拟导出过程
            export_data = {
                "version": version,
                "model_info": asdict(model_info),
                "export_time": time.time(),
                "samples_count": len(self.samples)
            }

            with open(export_path, 'wb') as f:
                pickle.dump(export_data, f)

            return {
                "status": "success",
                "export_path": export_path,
                "model_version": version
            }

        except Exception as e:
            self.logger.error(f"导出模型失败: {e}")
            return {"status": "error", "error": f"导出模型失败: {e}"}

    async def _cleanup_old_models(self, **kwargs) -> Dict[str, Any]:
        """清理旧模型"""
        try:
            # 保留最新的N个版本
            retention_count = self.config['model_retention_count']

            if len(self.model_versions) <= retention_count:
                return {"status": "success", "message": "无需清理"}

            # 按创建时间排序
            sorted_versions = sorted(
                self.model_versions.items(),
                key=lambda x: x[1].created_at,
                reverse=True
            )

            # 标记要删除的版本
            versions_to_deprecate = sorted_versions[retention_count:]

            removed_count = 0
            for version_id, version in versions_to_deprecate:
                version.status = 'deprecated'
                removed_count += 1

                # 删除检查点文件
                if version.checkpoint_path and Path(version.checkpoint_path).exists():
                    Path(version.checkpoint_path).unlink()

            await self._save_model_versions()

            return {
                "status": "success",
                "removed_count": removed_count,
                "retained_count": retention_count
            }

        except Exception as e:
            self.logger.error(f"清理旧模型失败: {e}")
            return {"status": "error", "error": f"清理旧模型失败: {e}"}

    async def _prepare_training_data(self) -> tuple:
        """准备训练数据"""
        # 简化的数据准备逻辑
        total_samples = len(self.samples)
        val_size = int(total_samples * self.config['validation_split'])
        test_size = int(total_samples * self.config['test_split'])
        train_size = total_samples - val_size - test_size

        # 模拟数据分割
        train_data = self.samples[:train_size]
        val_data = self.samples[train_size:train_size + val_size]
        test_data = self.samples[train_size + val_size:]

        return train_data, val_data, test_data

    def _get_latest_version(self) -> Optional[str]:
        """获取最新版本"""
        if not self.model_versions:
            return None

        return max(self.model_versions.keys(),
                  key=lambda x: self.model_versions[x].created_at)

    async def _save_samples(self):
        """保存样本到文件"""
        try:
            samples_file = Path(self.config['data_dir']) / 'training_samples.json'

            samples_data = [asdict(s) for s in self.samples]

            with open(samples_file, 'w', encoding='utf-8') as f:
                json.dump(samples_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"保存样本失败: {e}")

    async def _save_model_versions(self):
        """保存模型版本信息"""
        try:
            versions_file = Path(self.config['model_dir']) / 'model_versions.json'

            versions_data = {k: asdict(v) for k, v in self.model_versions.items()}

            with open(versions_file, 'w', encoding='utf-8') as f:
                json.dump(versions_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"保存模型版本失败: {e}")

    async def _load_data(self):
        """加载数据"""
        try:
            # 加载样本
            samples_file = Path(self.config['data_dir']) / 'training_samples.json'
            if samples_file.exists():
                with open(samples_file, 'r', encoding='utf-8') as f:
                    samples_data = json.load(f)
                    self.samples = [TrainingSample(**s) for s in samples_data]
                    self.stats['total_samples'] = len(self.samples)

            # 加载模型版本
            versions_file = Path(self.config['model_dir']) / 'model_versions.json'
            if versions_file.exists():
                with open(versions_file, 'r', encoding='utf-8') as f:
                    versions_data = json.load(f)
                    self.model_versions = {k: ModelVersion(**v) for k, v in versions_data.items()}

        except Exception as e:
            self.logger.error(f"加载数据失败: {e}")

    async def _auto_train(self):
        """自动训练"""
        try:
            self.logger.info("触发自动训练...")

            # 执行训练
            result = await self._train_model()

            if result['status'] == 'success':
                self.logger.info("自动训练完成")
            else:
                self.logger.warning(f"自动训练失败: {result.get('error', 'unknown')}")

        except Exception as e:
            self.logger.error(f"自动训练异常: {e}")

    async def start_background_tasks(self):
        """启动后台任务"""
        # 自动训练任务
        auto_train_task = asyncio.create_task(self._background_auto_train())
        self.background_tasks.append(auto_train_task)

        # 数据清理任务
        cleanup_task = asyncio.create_task(self._background_cleanup())
        self.background_tasks.append(cleanup_task)

    async def _background_auto_train(self):
        """后台自动训练"""
        while True:
            try:
                await asyncio.sleep(self.config['auto_training_interval'])

                if (len(self.samples) >= self.config['min_samples_for_training'] and
                    not self.training_active):
                    await self._auto_train()

            except Exception as e:
                self.logger.error(f"后台自动训练出错: {e}")
                await asyncio.sleep(60)

    async def _background_cleanup(self):
        """后台清理"""
        while True:
            try:
                await asyncio.sleep(86400)  # 每天清理一次
                await self._cleanup_old_models()
            except Exception as e:
                self.logger.error(f"后台清理出错: {e}")
                await asyncio.sleep(3600)