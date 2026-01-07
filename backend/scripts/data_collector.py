#!/usr/bin/env python3
"""
AI增强训练数据收集器
自动收集和标注训练数据，集成AI模型进行智能分析和逆向推理
"""

import asyncio
import json
import time
import random
import hashlib
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import re
import aiohttp

from backend.core.base import BaseScript
from backend.services.ai_service import AIService
from backend.scripts.ai_coordinator import AIModelCoordinator


@dataclass
class DataSource:
    """数据源"""
    name: str
    type: str  # 'web', 'api', 'file', 'database'
    url: Optional[str] = None
    config: Dict[str, Any] = None
    enabled: bool = True
    last_collected: Optional[float] = None
    collection_interval: int = 3600  # 1小时

    def __post_init__(self):
        if self.config is None:
            self.config = {}


@dataclass
class CollectedData:
    """收集的数据"""
    id: str
    source: str
    data_type: str  # 'text', 'image', 'tabular'
    content: Any
    metadata: Dict[str, Any]
    quality_score: float
    collected_at: float
    processed: bool = False
    ai_analysis: Optional[Dict[str, Any]] = None
    reverse_engineering: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.collected_at is None:
            self.collected_at = time.time()


class DataCollector(BaseScript):
    """AI增强数据收集器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 收集配置
        self.config = {
            'data_dir': 'backend/data/raw',
            'processed_dir': 'backend/data/processed',
            'max_raw_data': 50000,
            'collection_interval': 1800,  # 30分钟
            'quality_threshold': 0.6,
            'batch_size': 100,
            'auto_label': True,
            'label_sources': ['ai', 'rules', 'manual'],
            'data_retention_days': 30,
            'ai_enhanced': True,  # 启用AI增强
            'reverse_engineering': True,  # 启用逆向工程
        }

        # 数据源
        self.data_sources: Dict[str, DataSource] = {}

        # 收集的数据
        self.raw_data: List[CollectedData] = []
        self.processed_data: List[Dict[str, Any]] = []

        # AI服务用于自动标注
        self.ai_service = None

        # AI协调器用于智能分析
        self.ai_coordinator = None

        # 统计信息
        self.stats = {
            'total_collected': 0,
            'total_processed': 0,
            'quality_accepted': 0,
            'quality_rejected': 0,
            'auto_labeled': 0,
            'manual_labeled': 0,
            'collection_sessions': 0,
            'processing_time_avg': 0.0,
            'ai_analyzed': 0,
            'reverse_engineered': 0,
        }

        # 后台任务
        self.background_tasks = []

        # 创建目录
        self._ensure_directories()

    def _ensure_directories(self):
        """确保目录存在"""
        dirs = [
            self.config['data_dir'],
            self.config['processed_dir']
        ]
        for dir_path in dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """初始化数据收集器"""
        await super().initialize()

        # 初始化AI服务
        try:
            self.ai_service = AIService()
            await self.ai_service.initialize()
        except Exception as e:
            self.logger.warning(f"AI服务初始化失败: {e}")

        # 初始化AI协调器
        try:
            self.ai_coordinator = AIModelCoordinator()
            await self.ai_coordinator.initialize()
            self.logger.info("✅ AI协调器初始化成功")
        except Exception as e:
            self.logger.warning(f"AI协调器初始化失败: {e}")
            self.ai_coordinator = None

        # 加载数据源配置
        await self._load_data_sources()

        # 加载已收集的数据
        await self._load_collected_data()

        # 启动后台任务
        await self.start_background_tasks()

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行数据收集操作"""
        try:
            self.logger.info(f"执行数据收集操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'add_source':
                result = await self._add_data_source(**kwargs)
            elif action == 'collect_data':
                result = await self._collect_data(**kwargs)
            elif action == 'process_data':
                result = await self._process_data(**kwargs)
            elif action == 'label_data':
                result = await self._label_data(**kwargs)
            elif action == 'export_training_data':
                result = await self._export_training_data(**kwargs)
            elif action == 'list_sources':
                result = await self._list_data_sources()
            elif action == 'cleanup_old_data':
                result = await self._cleanup_old_data()
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

    async def _add_data_source(self, name: str, type: str, url: str = None,
                             config: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """添加数据源"""
        try:
            if name in self.data_sources:
                return {"status": "error", "error": f"数据源已存在: {name}"}

            source = DataSource(
                name=name,
                type=type,
                url=url,
                config=config or {}
            )

            self.data_sources[name] = source

            # 保存数据源配置
            await self._save_data_sources()

            return {
                "status": "success",
                "source": asdict(source)
            }

        except Exception as e:
            self.logger.error(f"添加数据源失败: {e}")
            return {"status": "error", "error": f"添加数据源失败: {e}"}

    async def _collect_data(self, source_name: str = None, **kwargs) -> Dict[str, Any]:
        """收集数据"""
        try:
            sources_to_collect = []

            if source_name:
                if source_name not in self.data_sources:
                    return {"status": "error", "error": f"数据源不存在: {source_name}"}
                sources_to_collect = [self.data_sources[source_name]]
            else:
                sources_to_collect = [s for s in self.data_sources.values() if s.enabled]

            total_collected = 0

            for source in sources_to_collect:
                # 检查是否需要收集
                if (source.last_collected and
                    time.time() - source.last_collected < source.collection_interval):
                    continue

                # 执行收集
                collected = await self._collect_from_source(source)
                total_collected += collected

                # 更新最后收集时间
                source.last_collected = time.time()

            # 保存数据源状态
            await self._save_data_sources()

            # 保存收集的数据
            await self._save_collected_data()

            self.stats['collection_sessions'] += 1

            return {
                "status": "success",
                "collected_count": total_collected,
                "total_raw_data": len(self.raw_data)
            }

        except Exception as e:
            self.logger.error(f"收集数据失败: {e}")
            return {"status": "error", "error": f"收集数据失败: {e}"}

    async def _collect_from_source(self, source: DataSource) -> int:
        """从数据源收集数据"""
        try:
            collected_count = 0

            if source.type == 'web':
                collected_count = await self._collect_from_web(source)
            elif source.type == 'api':
                collected_count = await self._collect_from_api(source)
            elif source.type == 'file':
                collected_count = await self._collect_from_file(source)
            elif source.type == 'database':
                collected_count = await self._collect_from_database(source)
            else:
                self.logger.warning(f"不支持的数据源类型: {source.type}")

            return collected_count

        except Exception as e:
            self.logger.error(f"从数据源 {source.name} 收集数据失败: {e}")
            return 0

    async def _collect_from_web(self, source: DataSource) -> int:
        """从网页收集数据 - AI增强版"""
        collected_count = 0

        try:
            # 使用AI协调器进行智能网页分析
            if self.ai_coordinator and self.config.get('ai_enhanced', True):
                # AI预分析：确定最佳收集策略
                strategy = await self._ai_analyze_collection_strategy(source)
                self.logger.info(f"AI分析收集策略: {strategy}")

                # 根据AI建议调整收集参数
                max_pages = strategy.get('max_pages', 10)
                focus_areas = strategy.get('focus_areas', ['content', 'metadata'])
            else:
                max_pages = 10
                focus_areas = ['content', 'metadata']

            # 执行智能数据收集
            for i in range(max_pages):
                # 生成模拟数据（实际实现中应该调用真实的爬虫）
                content = {
                    'title': f'AI分析网页标题 {i}',
                    'content': f'这是从 {source.name} 使用AI增强收集的网页内容示例 {i}',
                    'url': f'{source.url}/page/{i}',
                    'tags': ['web', 'ai-enhanced', 'intelligent-collection'],
                    'ai_generated': True
                }

                # AI内容分析
                if self.ai_coordinator and 'content' in focus_areas:
                    content_analysis = await self._ai_analyze_content(content['content'])
                    content['ai_analysis'] = content_analysis

                # AI元数据提取
                if self.ai_coordinator and 'metadata' in focus_areas:
                    metadata_analysis = await self._ai_extract_metadata(content)
                    content['ai_metadata'] = metadata_analysis

                data_id = f"web_ai_{source.name}_{int(time.time())}_{i}"
                collected_data = CollectedData(
                    id=data_id,
                    source=source.name,
                    data_type='text',
                    content=content,
                    metadata={
                        'source_type': 'web',
                        'url': content['url'],
                        'ai_enhanced': True,
                        'collection_strategy': strategy.get('strategy', 'default')
                    },
                    quality_score=random.uniform(0.7, 1.0)  # AI增强的数据质量更高
                )

                # AI质量评估
                if self.ai_coordinator:
                    quality_analysis = await self._ai_assess_quality(content)
                    collected_data.quality_score = quality_analysis.get('quality_score', collected_data.quality_score)
                    collected_data.ai_analysis = quality_analysis

                self.raw_data.append(collected_data)
                collected_count += 1

                # 实时逆向工程分析
                if self.config.get('reverse_engineering', True) and self.ai_coordinator:
                    reverse_analysis = await self._ai_reverse_engineer([collected_data])
                    collected_data.reverse_engineering = reverse_analysis
                    self.stats['reverse_engineered'] += 1

        except Exception as e:
            self.logger.error(f"AI增强网页数据收集失败: {e}")

        return collected_count

    async def _collect_from_api(self, source: DataSource) -> int:
        """从API收集数据"""
        # 模拟API数据收集
        collected_count = 0

        try:
            # 这里应该实现实际的API调用逻辑
            for i in range(random.randint(3, 15)):
                content = {
                    'data': f'API响应数据 {i}',
                    'endpoint': f'{source.url}/data/{i}',
                    'response_time': random.uniform(0.1, 2.0)
                }

                data_id = f"api_{source.name}_{int(time.time())}_{i}"
                collected_data = CollectedData(
                    id=data_id,
                    source=source.name,
                    data_type='tabular',
                    content=content,
                    metadata={'source_type': 'api', 'endpoint': content['endpoint']},
                    quality_score=random.uniform(0.6, 1.0)
                )

                self.raw_data.append(collected_data)
                collected_count += 1

        except Exception as e:
            self.logger.error(f"API数据收集失败: {e}")

        return collected_count

    async def _collect_from_file(self, source: DataSource) -> int:
        """从文件收集数据"""
        # 模拟文件数据收集
        collected_count = 0

        try:
            file_path = source.config.get('file_path')
            if not file_path or not Path(file_path).exists():
                return 0

            # 这里应该实现实际的文件读取逻辑
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for i, line in enumerate(lines[:random.randint(10, 50)]):
                content = {'line': line.strip(), 'line_number': i + 1}

                data_id = f"file_{source.name}_{int(time.time())}_{i}"
                collected_data = CollectedData(
                    id=data_id,
                    source=source.name,
                    data_type='text',
                    content=content,
                    metadata={'source_type': 'file', 'file_path': file_path},
                    quality_score=random.uniform(0.7, 1.0)
                )

                self.raw_data.append(collected_data)
                collected_count += 1

        except Exception as e:
            self.logger.error(f"文件数据收集失败: {e}")

        return collected_count

    async def _collect_from_database(self, source: DataSource) -> int:
        """从数据库收集数据"""
        # 模拟数据库数据收集
        collected_count = 0

        try:
            # 这里应该实现实际的数据库查询逻辑
            for i in range(random.randint(5, 25)):
                content = {
                    'record_id': i,
                    'field1': f'字段1值 {i}',
                    'field2': f'字段2值 {i}',
                    'timestamp': time.time()
                }

                data_id = f"db_{source.name}_{int(time.time())}_{i}"
                collected_data = CollectedData(
                    id=data_id,
                    source=source.name,
                    data_type='tabular',
                    content=content,
                    metadata={'source_type': 'database', 'table': source.config.get('table', 'unknown')},
                    quality_score=random.uniform(0.5, 1.0)
                )

                self.raw_data.append(collected_data)
                collected_count += 1

        except Exception as e:
            self.logger.error(f"数据库数据收集失败: {e}")

        return collected_count

    async def _process_data(self, batch_size: int = None, **kwargs) -> Dict[str, Any]:
        """处理数据"""
        try:
            batch_size = batch_size or self.config['batch_size']

            # 获取未处理的数据
            unprocessed = [d for d in self.raw_data if not d.processed]

            if not unprocessed:
                return {"status": "success", "message": "没有需要处理的数据"}

            # 分批处理
            processed_count = 0
            accepted_count = 0

            for i in range(0, len(unprocessed), batch_size):
                batch = unprocessed[i:i + batch_size]

                start_time = time.time()

                for data in batch:
                    try:
                        # 质量评估
                        quality_score = await self._assess_data_quality(data)

                        if quality_score >= self.config['quality_threshold']:
                            # 数据清洗和标准化
                            processed_data = await self._clean_and_normalize(data)

                            # 自动标注
                            if self.config['auto_label']:
                                processed_data = await self._auto_label_data(processed_data)

                            self.processed_data.append(processed_data)
                            accepted_count += 1
                            self.stats['quality_accepted'] += 1
                        else:
                            self.stats['quality_rejected'] += 1

                        data.processed = True
                        processed_count += 1

                    except Exception as e:
                        self.logger.error(f"处理数据 {data.id} 失败: {e}")
                        continue

                # 更新处理时间统计
                processing_time = time.time() - start_time
                self.stats['processing_time_avg'] = (
                    (self.stats['processing_time_avg'] * (self.stats['total_processed'] // batch_size) +
                     processing_time) /
                    ((self.stats['total_processed'] // batch_size) + 1)
                )

            self.stats['total_processed'] += processed_count

            # 保存处理后的数据
            await self._save_processed_data()

            # 限制原始数据数量
            if len(self.raw_data) > self.config['max_raw_data']:
                self.raw_data = self.raw_data[-self.config['max_raw_data']:]

            return {
                "status": "success",
                "processed_count": processed_count,
                "accepted_count": accepted_count,
                "total_processed": len(self.processed_data)
            }

        except Exception as e:
            self.logger.error(f"处理数据失败: {e}")
            return {"status": "error", "error": f"处理数据失败: {e}"}

    async def _assess_data_quality(self, data: CollectedData) -> float:
        """评估数据质量"""
        try:
            quality_score = data.quality_score

            # 基于内容长度的质量评估
            if data.data_type == 'text':
                content_length = len(str(data.content))
                if content_length < 10:
                    quality_score *= 0.5
                elif content_length > 1000:
                    quality_score *= 0.9
            elif data.data_type == 'image':
                # 图像质量评估（这里是简化的）
                quality_score *= 0.8
            elif data.data_type == 'tabular':
                # 表格数据质量评估
                if isinstance(data.content, dict) and len(data.content) > 3:
                    quality_score *= 0.9

            # 基于元数据的质量评估
            if data.metadata.get('error'):
                quality_score *= 0.3

            return min(quality_score, 1.0)

        except Exception as e:
            self.logger.error(f"评估数据质量失败: {e}")
            return 0.5

    async def _clean_and_normalize(self, data: CollectedData) -> Dict[str, Any]:
        """数据清洗和标准化"""
        try:
            processed = {
                'id': data.id,
                'source': data.source,
                'data_type': data.data_type,
                'original_content': data.content,
                'metadata': data.metadata,
                'quality_score': data.quality_score,
                'collected_at': data.collected_at,
                'processed_at': time.time()
            }

            if data.data_type == 'text':
                # 文本数据清洗
                if isinstance(data.content, dict):
                    text_content = data.content.get('content', str(data.content))
                else:
                    text_content = str(data.content)

                # 移除多余空白字符
                text_content = re.sub(r'\s+', ' ', text_content.strip())

                # 标准化长度
                if len(text_content) > 2000:
                    text_content = text_content[:2000] + '...'

                processed['cleaned_content'] = text_content
                processed['content_length'] = len(text_content)

            elif data.data_type == 'tabular':
                # 表格数据标准化
                if isinstance(data.content, dict):
                    # 移除空值字段
                    cleaned_content = {k: v for k, v in data.content.items() if v is not None}
                    processed['cleaned_content'] = cleaned_content
                    processed['field_count'] = len(cleaned_content)

            else:
                processed['cleaned_content'] = data.content

            return processed

        except Exception as e:
            self.logger.error(f"数据清洗失败: {e}")
            return {
                'id': data.id,
                'source': data.source,
                'data_type': data.data_type,
                'cleaned_content': data.content,
                'metadata': data.metadata,
                'quality_score': data.quality_score,
                'collected_at': data.collected_at,
                'processed_at': time.time(),
                'error': str(e)
            }

    async def _auto_label_data(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """自动标注数据"""
        try:
            if not self.ai_service:
                return processed_data

            content = processed_data.get('cleaned_content', '')

            if processed_data['data_type'] == 'text':
                # 使用AI进行文本分类和标注
                labels = await self.ai_service.classify_text(str(content))
                processed_data['auto_labels'] = labels
                processed_data['labeled_by'] = 'ai'
                self.stats['auto_labeled'] += 1

            elif processed_data['data_type'] == 'tabular':
                # 表格数据标注
                processed_data['auto_labels'] = ['structured_data']
                processed_data['labeled_by'] = 'rules'

            return processed_data

        except Exception as e:
            self.logger.error(f"自动标注失败: {e}")
            processed_data['labeling_error'] = str(e)
            return processed_data

    async def _label_data(self, data_ids: List[str], labels: Dict[str, Any],
                        labeler: str = 'manual', **kwargs) -> Dict[str, Any]:
        """手动标注数据"""
        try:
            labeled_count = 0

            for data_id in data_ids:
                # 查找数据
                data = None
                for item in self.processed_data:
                    if item['id'] == data_id:
                        data = item
                        break

                if not data:
                    continue

                # 添加标注
                data['manual_labels'] = labels
                data['labeled_by'] = labeler
                data['labeled_at'] = time.time()

                labeled_count += 1
                self.stats['manual_labeled'] += 1

            # 保存标注后的数据
            await self._save_processed_data()

            return {
                "status": "success",
                "labeled_count": labeled_count
            }

        except Exception as e:
            self.logger.error(f"手动标注失败: {e}")
            return {"status": "error", "error": f"手动标注失败: {e}"}

    async def _export_training_data(self, output_path: str = None,
                                  data_types: List[str] = None, **kwargs) -> Dict[str, Any]:
        """导出训练数据"""
        try:
            if not output_path:
                timestamp = int(time.time())
                output_path = f"{self.config['processed_dir']}/training_data_{timestamp}.json"

            # 筛选数据
            export_data = self.processed_data

            if data_types:
                export_data = [d for d in export_data if d['data_type'] in data_types]

            # 转换为训练格式
            training_samples = []
            for item in export_data:
                sample = {
                    'id': item['id'],
                    'input_data': item.get('cleaned_content', item.get('original_content')),
                    'target_output': item.get('manual_labels') or item.get('auto_labels', {}),
                    'sample_type': item['data_type'],
                    'quality_score': item['quality_score'],
                    'source': item['source'],
                    'timestamp': item['collected_at'],
                    'metadata': item.get('metadata', {})
                }
                training_samples.append(sample)

            # 保存到文件
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(training_samples, f, ensure_ascii=False, indent=2)

            return {
                "status": "success",
                "export_path": output_path,
                "exported_count": len(training_samples),
                "data_types": list(set(d['data_type'] for d in export_data))
            }

        except Exception as e:
            self.logger.error(f"导出训练数据失败: {e}")
            return {"status": "error", "error": f"导出训练数据失败: {e}"}

    async def _list_data_sources(self, **kwargs) -> Dict[str, Any]:
        """列出数据源"""
        try:
            sources_data = [asdict(s) for s in self.data_sources.values()]

            return {
                "status": "success",
                "sources": sources_data,
                "total_sources": len(sources_data),
                "enabled_sources": len([s for s in sources_data if s['enabled']])
            }

        except Exception as e:
            self.logger.error(f"列出数据源失败: {e}")
            return {"status": "error", "error": f"列出数据源失败: {e}"}

    async def _cleanup_old_data(self, days: int = None, **kwargs) -> Dict[str, Any]:
        """清理旧数据"""
        try:
            retention_days = days or self.config['data_retention_days']
            cutoff_time = time.time() - (retention_days * 24 * 3600)

            # 清理原始数据
            original_count = len(self.raw_data)
            self.raw_data = [d for d in self.raw_data if d.collected_at > cutoff_time]
            raw_removed = original_count - len(self.raw_data)

            # 清理处理后的数据
            original_count = len(self.processed_data)
            self.processed_data = [d for d in self.processed_data if d.get('collected_at', 0) > cutoff_time]
            processed_removed = original_count - len(self.processed_data)

            # 保存清理后的数据
            await self._save_collected_data()
            await self._save_processed_data()

            return {
                "status": "success",
                "raw_data_removed": raw_removed,
                "processed_data_removed": processed_removed,
                "remaining_raw": len(self.raw_data),
                "remaining_processed": len(self.processed_data)
            }

        except Exception as e:
            self.logger.error(f"清理旧数据失败: {e}")
            return {"status": "error", "error": f"清理旧数据失败: {e}"}

    async def _save_data_sources(self):
        """保存数据源配置"""
        try:
            sources_file = Path(self.config['data_dir']) / 'data_sources.json'

            sources_data = {k: asdict(v) for k, v in self.data_sources.items()}

            with open(sources_file, 'w', encoding='utf-8') as f:
                json.dump(sources_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"保存数据源配置失败: {e}")

    async def _save_collected_data(self):
        """保存收集的数据"""
        try:
            data_file = Path(self.config['data_dir']) / 'collected_data.json'

            data_list = [asdict(d) for d in self.raw_data]

            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data_list, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"保存收集数据失败: {e}")

    async def _save_processed_data(self):
        """保存处理后的数据"""
        try:
            data_file = Path(self.config['processed_dir']) / 'processed_data.json'

            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(self.processed_data, f, ensure_ascii=False, indent=2)

        except Exception as e:
            self.logger.error(f"保存处理数据失败: {e}")

    async def _load_data_sources(self):
        """加载数据源配置"""
        try:
            sources_file = Path(self.config['data_dir']) / 'data_sources.json'
            if sources_file.exists():
                with open(sources_file, 'r', encoding='utf-8') as f:
                    sources_data = json.load(f)
                    self.data_sources = {k: DataSource(**v) for k, v in sources_data.items()}

        except Exception as e:
            self.logger.error(f"加载数据源配置失败: {e}")

    async def _load_collected_data(self):
        """加载收集的数据"""
        try:
            # 加载原始数据
            data_file = Path(self.config['data_dir']) / 'collected_data.json'
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    data_list = json.load(f)
                    self.raw_data = [CollectedData(**d) for d in data_list]
                    self.stats['total_collected'] = len(self.raw_data)

            # 加载处理后的数据
            processed_file = Path(self.config['processed_dir']) / 'processed_data.json'
            if processed_file.exists():
                with open(processed_file, 'r', encoding='utf-8') as f:
                    self.processed_data = json.load(f)
                    self.stats['total_processed'] = len(self.processed_data)

        except Exception as e:
            self.logger.error(f"加载收集数据失败: {e}")

    async def start_background_tasks(self):
        """启动后台任务"""
        # 自动收集任务
        auto_collect_task = asyncio.create_task(self._background_collection())
        self.background_tasks.append(auto_collect_task)

        # 自动处理任务
        auto_process_task = asyncio.create_task(self._background_processing())
        self.background_tasks.append(auto_process_task)

        # 数据清理任务
        cleanup_task = asyncio.create_task(self._background_cleanup())
        self.background_tasks.append(cleanup_task)

    async def _background_collection(self):
        """后台自动收集"""
        while True:
            try:
                await asyncio.sleep(self.config['collection_interval'])
                await self._collect_data()
            except Exception as e:
                self.logger.error(f"后台收集出错: {e}")
                await asyncio.sleep(300)  # 5分钟后重试

    async def _background_processing(self):
        """后台自动处理"""
        while True:
            try:
                await asyncio.sleep(600)  # 10分钟处理一次
                await self._process_data()
            except Exception as e:
                self.logger.error(f"后台处理出错: {e}")
                await asyncio.sleep(300)

    async def _background_cleanup(self):
        """后台清理"""
        while True:
            try:
                await asyncio.sleep(86400)  # 每天清理一次
                await self._cleanup_old_data()
            except Exception as e:
                self.logger.error(f"后台清理出错: {e}")
                await asyncio.sleep(3600)

    # ============= AI增强方法 =============

    async def _ai_analyze_collection_strategy(self, source: DataSource) -> Dict[str, Any]:
        """AI分析收集策略"""
        if not self.ai_coordinator:
            return {
                'strategy': 'default',
                'max_pages': 10,
                'focus_areas': ['content', 'metadata']
            }

        try:
            prompt = f"""
            分析数据源收集策略：
            数据源: {source.name}
            类型: {source.type}
            URL: {source.url}
            配置: {source.config}

            请制定最佳收集策略：
            1. 建议收集页数
            2. 重点关注领域
            3. 数据质量标准
            4. 收集频率建议
            """

            result = await self.ai_coordinator.run('task_planning', content=prompt)

            if result.get('status') == 'success':
                strategy = result.get('result', {})
                return {
                    'strategy': 'ai_optimized',
                    'max_pages': strategy.get('max_pages', 10),
                    'focus_areas': strategy.get('focus_areas', ['content', 'metadata']),
                    'quality_threshold': strategy.get('quality_threshold', 0.7),
                    'collection_frequency': strategy.get('collection_frequency', 1800)
                }
            else:
                return {
                    'strategy': 'default',
                    'max_pages': 10,
                    'focus_areas': ['content', 'metadata']
                }

        except Exception as e:
            self.logger.error(f"AI收集策略分析失败: {e}")
            return {
                'strategy': 'fallback',
                'max_pages': 5,
                'focus_areas': ['content']
            }

    async def _ai_analyze_content(self, content: str) -> Dict[str, Any]:
        """AI内容分析"""
        if not self.ai_coordinator:
            return {'summary': 'AI未启用'}

        try:
            prompt = f"请分析以下内容，提取关键信息和主题：\n\n{content[:1000]}"

            result = await self.ai_coordinator.run('analyze_content', content=prompt)

            if result.get('status') == 'success':
                return result.get('result', {})
            else:
                return {'summary': 'AI分析失败'}

        except Exception as e:
            self.logger.error(f"AI内容分析失败: {e}")
            return {'error': str(e)}

    async def _ai_extract_metadata(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """AI元数据提取"""
        if not self.ai_coordinator:
            return {'metadata': 'AI未启用'}

        try:
            content_str = json.dumps(content, ensure_ascii=False)
            prompt = f"从以下内容中提取结构化元数据：\n\n{content_str[:1500]}"

            result = await self.ai_coordinator.run('analyze_content', content=prompt)

            if result.get('status') == 'success':
                return result.get('result', {})
            else:
                return {'metadata': 'AI提取失败'}

        except Exception as e:
            self.logger.error(f"AI元数据提取失败: {e}")
            return {'error': str(e)}

    async def _ai_assess_quality(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """AI质量评估"""
        if not self.ai_coordinator:
            return {'quality_score': 0.5, 'assessment': 'AI未启用'}

        try:
            content_str = json.dumps(content, ensure_ascii=False)
            prompt = f"评估以下内容的质量和价值（0-1分）：\n\n{content_str[:1000]}"

            result = await self.ai_coordinator.run('analyze_content', content=prompt)

            if result.get('status') == 'success':
                analysis = result.get('result', {})
                return {
                    'quality_score': analysis.get('quality_score', 0.5),
                    'assessment': analysis.get('assessment', '一般'),
                    'strengths': analysis.get('strengths', []),
                    'weaknesses': analysis.get('weaknesses', [])
                }
            else:
                return {'quality_score': 0.5, 'assessment': 'AI评估失败'}

        except Exception as e:
            self.logger.error(f"AI质量评估失败: {e}")
            return {'quality_score': 0.3, 'assessment': f'评估异常: {str(e)}'}

    async def _ai_reverse_engineer(self, data_items: List[CollectedData]) -> Dict[str, Any]:
        """AI逆向工程分析"""
        if not self.ai_coordinator:
            return {'reverse_engineering': 'AI未启用'}

        try:
            # 汇总数据特征
            data_summary = {
                'total_items': len(data_items),
                'sources': list(set(item.source for item in data_items)),
                'data_types': list(set(item.data_type for item in data_items)),
                'avg_quality': sum(item.quality_score for item in data_items) / len(data_items),
                'sample_content': [item.content for item in data_items[:3]]  # 取前3个样本
            }

            prompt = f"""
            基于收集的数据进行逆向工程分析：
            数据汇总: {json.dumps(data_summary, ensure_ascii=False, indent=2)}

            请分析：
            1. 数据源架构模式
            2. 潜在的API结构
            3. 数据生成模式
            4. 系统集成可能性
            5. 扩展和优化建议
            """

            result = await self.ai_coordinator.run('complex_reasoning', content=prompt)

            if result.get('status') == 'success':
                return result.get('result', {})
            else:
                return {'reverse_engineering': 'AI分析失败'}

        except Exception as e:
            self.logger.error(f"AI逆向工程分析失败: {e}")
            return {'error': str(e)}

    async def _ai_generate_insights(self) -> Dict[str, Any]:
        """AI生成数据洞察"""
        if not self.ai_coordinator:
            return {'insights': 'AI未启用'}

        try:
            # 分析整体数据统计
            stats_summary = {
                'total_collected': self.stats['total_collected'],
                'total_processed': self.stats['total_processed'],
                'ai_analyzed': self.stats['ai_analyzed'],
                'reverse_engineered': self.stats['reverse_engineered'],
                'quality_avg': sum(d.quality_score for d in self.raw_data) / len(self.raw_data) if self.raw_data else 0,
                'data_sources': len(self.data_sources),
                'collection_sessions': self.stats['collection_sessions']
            }

            prompt = f"""
            基于数据收集统计生成洞察报告：
            统计数据: {json.dumps(stats_summary, ensure_ascii=False, indent=2)}

            请生成：
            1. 数据收集效果评估
            2. AI增强效果分析
            3. 改进建议
            4. 未来优化方向
            """

            result = await self.ai_coordinator.run('complex_reasoning', content=prompt)

            if result.get('status') == 'success':
                return result.get('result', {})
            else:
                return {'insights': 'AI洞察生成失败'}

        except Exception as e:
            self.logger.error(f"AI洞察生成失败: {e}")
            return {'error': str(e)}