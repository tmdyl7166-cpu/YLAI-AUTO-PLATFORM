#!/usr/bin/env python3
"""
分布式采集框架 - 结果聚合器
合并分布式结果、数据去重和一致性校验
"""

import asyncio
import json
import time
import hashlib
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import threading
import queue

from backend.core.base import BaseScript


@dataclass
class AggregatedResult:
    """聚合结果"""
    task_id: str
    task_type: str
    status: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: float = None
    updated_at: float = None
    version: int = 1
    checksum: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.updated_at is None:
            self.updated_at = time.time()
        if not self.checksum:
            self.checksum = self._calculate_checksum()

    def _calculate_checksum(self) -> str:
        """计算数据校验和"""
        data_str = json.dumps(self.data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()

    def update_data(self, new_data: Dict[str, Any], merge_strategy: str = 'replace'):
        """更新数据"""
        if merge_strategy == 'merge':
            self._merge_data(new_data)
        elif merge_strategy == 'replace':
            self.data = new_data
        elif merge_strategy == 'append':
            self._append_data(new_data)

        self.updated_at = time.time()
        self.version += 1
        self.checksum = self._calculate_checksum()

    def _merge_data(self, new_data: Dict[str, Any]):
        """合并数据"""
        def merge_dicts(d1, d2):
            for key, value in d2.items():
                if key in d1 and isinstance(d1[key], dict) and isinstance(value, dict):
                    merge_dicts(d1[key], value)
                elif key in d1 and isinstance(d1[key], list) and isinstance(value, list):
                    d1[key].extend(value)
                else:
                    d1[key] = value

        merge_dicts(self.data, new_data)

    def _append_data(self, new_data: Dict[str, Any]):
        """追加数据"""
        for key, value in new_data.items():
            if key not in self.data:
                self.data[key] = value
            elif isinstance(self.data[key], list):
                if isinstance(value, list):
                    self.data[key].extend(value)
                else:
                    self.data[key].append(value)
            else:
                # 转换为列表
                self.data[key] = [self.data[key], value]


class ResultAggregator(BaseScript):
    """结果聚合器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 结果存储
        self.results: Dict[str, AggregatedResult] = {}

        # 去重缓存
        self.duplicate_cache: Set[str] = set()

        # 实时更新队列
        self.update_queue = asyncio.Queue()

        # WebSocket连接管理（预留）
        self.websocket_clients: Set[Any] = set()

        # 配置
        self.config = {
            'deduplication_enabled': True,
            'real_time_updates': True,
            'max_results': 10000,
            'cleanup_interval': 3600,  # 1小时清理一次
            'merge_strategy': 'merge',  # merge, replace, append
            'consistency_check': True,
            'batch_size': 100
        }

        # 统计信息
        self.stats = {
            'total_results': 0,
            'unique_results': 0,
            'duplicate_results': 0,
            'merged_results': 0,
            'failed_results': 0,
            'avg_processing_time': 0.0,
            'realtime_updates': 0
        }

        # 后台任务
        self.background_tasks = []

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行结果聚合操作"""
        try:
            self.logger.info(f"执行结果聚合操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'aggregate_result':
                result = await self._aggregate_result(**kwargs)
            elif action == 'get_result':
                result = await self._get_result(**kwargs)
            elif action == 'list_results':
                result = await self._list_results(**kwargs)
            elif action == 'search_results':
                result = await self._search_results(**kwargs)
            elif action == 'export_results':
                result = await self._export_results(**kwargs)
            elif action == 'cleanup':
                result = await self._cleanup(**kwargs)
            elif action == 'consistency_check':
                result = await self._consistency_check()
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

    async def _aggregate_result(self, task_id: str, task_type: str,
                              result_data: Dict[str, Any], metadata: Dict[str, Any] = None,
                              **kwargs) -> Dict[str, Any]:
        """聚合单个结果"""
        start_time = time.time()

        try:
            # 去重检查
            if self.config['deduplication_enabled']:
                duplicate_key = self._generate_duplicate_key(result_data)
                if duplicate_key in self.duplicate_cache:
                    self.stats['duplicate_results'] += 1
                    return {
                        "status": "duplicate",
                        "task_id": task_id,
                        "message": "结果已存在，跳过去重"
                    }

            # 检查是否已存在结果
            if task_id in self.results:
                # 合并现有结果
                existing_result = self.results[task_id]
                existing_result.update_data(result_data, self.config['merge_strategy'])
                self.stats['merged_results'] += 1

                # 添加到去重缓存
                if self.config['deduplication_enabled']:
                    self.duplicate_cache.add(duplicate_key)

                # 实时更新通知
                if self.config['real_time_updates']:
                    await self._notify_realtime_update(task_id, existing_result)

                processing_time = time.time() - start_time

                return {
                    "status": "merged",
                    "task_id": task_id,
                    "action": "update",
                    "processing_time": round(processing_time, 3)
                }

            else:
                # 创建新结果
                result = AggregatedResult(
                    task_id=task_id,
                    task_type=task_type,
                    status="completed",
                    data=result_data,
                    metadata=metadata or {}
                )

                self.results[task_id] = result
                self.stats['total_results'] += 1
                self.stats['unique_results'] += 1

                # 添加到去重缓存
                if self.config['deduplication_enabled']:
                    self.duplicate_cache.add(duplicate_key)

                # 检查结果数量限制
                if len(self.results) > self.config['max_results']:
                    await self._cleanup_old_results()

                # 实时更新通知
                if self.config['real_time_updates']:
                    await self._notify_realtime_update(task_id, result)

                processing_time = time.time() - start_time

                return {
                    "status": "success",
                    "task_id": task_id,
                    "action": "create",
                    "processing_time": round(processing_time, 3)
                }

        except Exception as e:
            self.stats['failed_results'] += 1
            processing_time = time.time() - start_time

            self.logger.error(f"聚合结果失败: {e}")

            return {
                "status": "error",
                "task_id": task_id,
                "error": str(e),
                "processing_time": round(processing_time, 3)
            }

    async def _get_result(self, task_id: str, **kwargs) -> Dict[str, Any]:
        """获取单个结果"""
        try:
            if task_id not in self.results:
                return {"status": "error", "error": "结果不存在"}

            result = self.results[task_id]

            return {
                "status": "success",
                "result": asdict(result)
            }

        except Exception as e:
            self.logger.error(f"获取结果失败: {e}")
            return {"status": "error", "error": f"获取结果失败: {e}"}

    async def _list_results(self, task_type: str = None, status: str = None,
                          limit: int = 100, offset: int = 0, **kwargs) -> Dict[str, Any]:
        """列出结果"""
        try:
            results = []

            for result in self.results.values():
                # 过滤条件
                if task_type and result.task_type != task_type:
                    continue
                if status and result.status != status:
                    continue

                results.append(asdict(result))

            # 分页
            total = len(results)
            paginated_results = results[offset:offset + limit]

            return {
                "status": "success",
                "total": total,
                "limit": limit,
                "offset": offset,
                "results": paginated_results
            }

        except Exception as e:
            self.logger.error(f"列出结果失败: {e}")
            return {"status": "error", "error": f"列出结果失败: {e}"}

    async def _search_results(self, query: str, fields: List[str] = None,
                            **kwargs) -> Dict[str, Any]:
        """搜索结果"""
        try:
            if not query:
                return {"status": "error", "error": "查询不能为空"}

            matching_results = []
            search_fields = fields or ['data', 'metadata']

            for result in self.results.values():
                if self._matches_query(result, query, search_fields):
                    matching_results.append(asdict(result))

            return {
                "status": "success",
                "query": query,
                "total_matches": len(matching_results),
                "results": matching_results[:100]  # 限制返回数量
            }

        except Exception as e:
            self.logger.error(f"搜索结果失败: {e}")
            return {"status": "error", "error": f"搜索结果失败: {e}"}

    def _matches_query(self, result: AggregatedResult, query: str, fields: List[str]) -> bool:
        """检查结果是否匹配查询"""
        query_lower = query.lower()

        for field in fields:
            if field == 'data':
                data_str = json.dumps(result.data, default=str).lower()
                if query_lower in data_str:
                    return True
            elif field == 'metadata':
                metadata_str = json.dumps(result.metadata, default=str).lower()
                if query_lower in metadata_str:
                    return True

        return False

    async def _export_results(self, format_type: str = 'json', task_type: str = None,
                            **kwargs) -> Dict[str, Any]:
        """导出结果"""
        try:
            # 筛选结果
            results_to_export = []
            for result in self.results.values():
                if task_type and result.task_type != task_type:
                    continue
                results_to_export.append(asdict(result))

            if format_type == 'json':
                export_data = {
                    "export_time": time.time(),
                    "total_results": len(results_to_export),
                    "results": results_to_export
                }
                content = json.dumps(export_data, indent=2, default=str)

            elif format_type == 'csv':
                # 简化的CSV导出
                if results_to_export:
                    headers = list(results_to_export[0].keys())
                    content = ','.join(headers) + '\n'

                    for result in results_to_export:
                        row = [str(result.get(h, '')) for h in headers]
                        content += ','.join(row) + '\n'
                else:
                    content = ""

            else:
                return {"status": "error", "error": f"不支持的导出格式: {format_type}"}

            return {
                "status": "success",
                "format": format_type,
                "total_results": len(results_to_export),
                "content": content,
                "content_length": len(content)
            }

        except Exception as e:
            self.logger.error(f"导出结果失败: {e}")
            return {"status": "error", "error": f"导出结果失败: {e}"}

    async def _cleanup(self, max_age: int = 86400, **kwargs) -> Dict[str, Any]:
        """清理过期结果"""
        try:
            current_time = time.time()
            removed_count = 0

            results_to_remove = []
            for task_id, result in self.results.items():
                if current_time - result.updated_at > max_age:
                    results_to_remove.append(task_id)

            for task_id in results_to_remove:
                del self.results[task_id]
                removed_count += 1

            # 清理去重缓存（保留最近的）
            if len(self.duplicate_cache) > 10000:
                # 保留最新的5000个
                self.duplicate_cache = set(list(self.duplicate_cache)[-5000:])

            return {
                "status": "success",
                "removed_count": removed_count,
                "remaining_count": len(self.results)
            }

        except Exception as e:
            self.logger.error(f"清理结果失败: {e}")
            return {"status": "error", "error": f"清理结果失败: {e}"}

    async def _consistency_check(self) -> Dict[str, Any]:
        """一致性校验"""
        try:
            inconsistencies = []

            for task_id, result in self.results.items():
                # 检查校验和
                current_checksum = result._calculate_checksum()
                if current_checksum != result.checksum:
                    inconsistencies.append({
                        "task_id": task_id,
                        "type": "checksum_mismatch",
                        "expected": result.checksum,
                        "actual": current_checksum
                    })

                # 检查数据完整性
                if not result.data:
                    inconsistencies.append({
                        "task_id": task_id,
                        "type": "empty_data"
                    })

            return {
                "status": "success",
                "total_checked": len(self.results),
                "inconsistencies": inconsistencies,
                "consistency_rate": (len(self.results) - len(inconsistencies)) / max(len(self.results), 1)
            }

        except Exception as e:
            self.logger.error(f"一致性校验失败: {e}")
            return {"status": "error", "error": f"一致性校验失败: {e}"}

    def _generate_duplicate_key(self, data: Dict[str, Any]) -> str:
        """生成去重键"""
        # 使用数据的重要字段生成去重键
        key_parts = []

        # 尝试提取URL
        if 'url' in data:
            key_parts.append(str(data['url']))

        # 尝试提取标题或主要内容
        if 'title' in data:
            key_parts.append(str(data['title']))
        elif 'content' in data and len(str(data['content'])) > 50:
            key_parts.append(str(data['content'])[:100])

        # 如果没有足够的信息，使用整个数据的哈希
        if not key_parts:
            data_str = json.dumps(data, sort_keys=True)
            return hashlib.md5(data_str.encode()).hexdigest()

        return hashlib.md5('|'.join(key_parts).encode()).hexdigest()

    async def _notify_realtime_update(self, task_id: str, result: AggregatedResult):
        """通知实时更新"""
        try:
            update_data = {
                "type": "result_update",
                "task_id": task_id,
                "timestamp": time.time(),
                "result": asdict(result)
            }

            # 添加到更新队列
            await self.update_queue.put(update_data)
            self.stats['realtime_updates'] += 1

            # 通知WebSocket客户端（预留）
            # for client in self.websocket_clients:
            #     await client.send_json(update_data)

        except Exception as e:
            self.logger.warning(f"实时更新通知失败: {e}")

    async def _cleanup_old_results(self):
        """清理旧结果以控制内存使用"""
        try:
            # 按更新时间排序，保留最新的结果
            sorted_results = sorted(
                self.results.items(),
                key=lambda x: x[1].updated_at,
                reverse=True
            )

            # 保留最新的80%结果
            keep_count = int(self.config['max_results'] * 0.8)
            results_to_remove = sorted_results[keep_count:]

            for task_id, _ in results_to_remove:
                del self.results[task_id]

            self.logger.info(f"清理了 {len(results_to_remove)} 个旧结果")

        except Exception as e:
            self.logger.error(f"清理旧结果失败: {e}")

    async def batch_aggregate(self, results_batch: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """批量聚合结果"""
        successful = 0
        failed = 0
        duplicates = 0

        for result_data in results_batch:
            result = await self._aggregate_result(**result_data, **kwargs)

            if result['status'] == 'success':
                successful += 1
            elif result['status'] == 'duplicate':
                duplicates += 1
            else:
                failed += 1

        return {
            "status": "success",
            "total_processed": len(results_batch),
            "successful": successful,
            "duplicates": duplicates,
            "failed": failed
        }

    async def get_realtime_updates(self, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """获取实时更新（用于WebSocket）"""
        try:
            update = await asyncio.wait_for(
                self.update_queue.get(),
                timeout=timeout
            )
            return update
        except asyncio.TimeoutError:
            return None

    async def start_background_tasks(self):
        """启动后台任务"""
        # 定期清理任务
        cleanup_task = asyncio.create_task(self._background_cleanup())
        self.background_tasks.append(cleanup_task)

        # 一致性检查任务
        if self.config['consistency_check']:
            consistency_task = asyncio.create_task(self._background_consistency_check())
            self.background_tasks.append(consistency_task)

    async def _background_cleanup(self):
        """后台清理任务"""
        while True:
            try:
                await self._cleanup()
                await asyncio.sleep(self.config['cleanup_interval'])
            except Exception as e:
                self.logger.error(f"后台清理出错: {e}")
                await asyncio.sleep(60)

    async def _background_consistency_check(self):
        """后台一致性检查"""
        while True:
            try:
                check_result = await self._consistency_check()
                if check_result.get('inconsistencies'):
                    self.logger.warning(f"发现 {len(check_result['inconsistencies'])} 个一致性问题")
                await asyncio.sleep(3600)  # 每小时检查一次
            except Exception as e:
                self.logger.error(f"后台一致性检查出错: {e}")
                await asyncio.sleep(60)