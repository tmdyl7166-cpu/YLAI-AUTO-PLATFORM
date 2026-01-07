#!/usr/bin/env python3
"""
分布式采集框架 - 节点管理器
管理分布式节点注册、心跳检测和负载均衡
"""

import asyncio
import json
import time
import uuid
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import socket
import psutil

from backend.core.base import BaseScript


@dataclass
class NodeInfo:
    """节点信息"""
    node_id: str
    hostname: str
    ip_address: str
    port: int
    status: str = 'active'  # active, inactive, overloaded, failed
    capabilities: List[str] = None  # ['crawl', 'analyze', 'validate']
    max_concurrent_tasks: int = 5
    current_tasks: int = 0
    total_tasks_processed: int = 0
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_bandwidth: float = 0.0
    registered_at: float = None
    last_heartbeat: float = None
    heartbeat_interval: int = 30  # seconds
    tags: List[str] = None  # ['gpu', 'high_memory', 'fast_network']

    def __post_init__(self):
        if self.registered_at is None:
            self.registered_at = time.time()
        if self.last_heartbeat is None:
            self.last_heartbeat = time.time()
        if self.capabilities is None:
            self.capabilities = ['crawl']
        if self.tags is None:
            self.tags = []


@dataclass
class LoadBalanceResult:
    """负载均衡结果"""
    node_id: str
    score: float
    reason: str


class NodeManager(BaseScript):
    """节点管理器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 节点存储
        self.nodes: Dict[str, NodeInfo] = {}

        # 配置
        self.config = {
            'heartbeat_timeout': 90,  # 心跳超时时间(秒)
            'max_nodes': 100,         # 最大节点数
            'auto_scaling': True,     # 自动扩容
            'load_balance_strategy': 'weighted_round_robin',  # 负载均衡策略
            'health_check_interval': 60,  # 健康检查间隔
            'node_cleanup_interval': 300,  # 节点清理间隔
        }

        # 负载均衡历史
        self.load_balance_history: List[Dict[str, Any]] = []

        # 统计信息
        self.stats = {
            'total_nodes': 0,
            'active_nodes': 0,
            'total_capacity': 0,
            'used_capacity': 0,
            'avg_load': 0.0,
            'failed_heartbeats': 0
        }

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行节点管理操作"""
        try:
            self.logger.info(f"执行节点管理操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'register_node':
                result = await self._register_node(**kwargs)
            elif action == 'unregister_node':
                result = await self._unregister_node(**kwargs)
            elif action == 'heartbeat':
                result = await self._heartbeat(**kwargs)
            elif action == 'get_node':
                result = await self._get_node(**kwargs)
            elif action == 'list_nodes':
                result = await self._list_nodes(**kwargs)
            elif action == 'load_balance':
                result = await self._load_balance(**kwargs)
            elif action == 'health_check':
                result = await self._health_check()
            elif action == 'scale_nodes':
                result = await self._scale_nodes(**kwargs)
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

    async def _register_node(self, hostname: str = None, port: int = 8080,
                           capabilities: List[str] = None, max_concurrent: int = 5,
                           tags: List[str] = None, **kwargs) -> Dict[str, Any]:
        """注册新节点"""
        try:
            # 获取本机信息
            if hostname is None:
                hostname = socket.gethostname()

            ip_address = self._get_local_ip()

            # 检查节点数量限制
            if len(self.nodes) >= self.config['max_nodes']:
                return {
                    "status": "error",
                    "error": f"已达到最大节点数限制: {self.config['max_nodes']}"
                }

            # 生成节点ID
            node_id = str(uuid.uuid4())

            # 创建节点信息
            node = NodeInfo(
                node_id=node_id,
                hostname=hostname,
                ip_address=ip_address,
                port=port,
                capabilities=capabilities or ['crawl'],
                max_concurrent_tasks=max_concurrent,
                tags=tags or []
            )

            # 更新系统资源信息
            await self._update_node_resources(node)

            # 存储节点
            self.nodes[node_id] = node

            # 更新统计
            self._update_stats()

            self.logger.info(f"节点注册成功: {node_id} ({hostname}:{port})")

            return {
                "status": "success",
                "node_id": node_id,
                "node_info": asdict(node),
                "message": "节点注册成功"
            }

        except Exception as e:
            self.logger.error(f"节点注册失败: {e}")
            return {"status": "error", "error": f"节点注册失败: {e}"}

    async def _unregister_node(self, node_id: str, **kwargs) -> Dict[str, Any]:
        """注销节点"""
        try:
            if node_id not in self.nodes:
                return {"status": "error", "error": "节点不存在"}

            node = self.nodes[node_id]

            # 检查是否有正在运行的任务
            if node.current_tasks > 0:
                return {
                    "status": "error",
                    "error": f"节点仍有 {node.current_tasks} 个正在运行的任务"
                }

            # 移除节点
            del self.nodes[node_id]

            # 更新统计
            self._update_stats()

            self.logger.info(f"节点注销成功: {node_id}")

            return {
                "status": "success",
                "node_id": node_id,
                "message": "节点注销成功"
            }

        except Exception as e:
            self.logger.error(f"节点注销失败: {e}")
            return {"status": "error", "error": f"节点注销失败: {e}"}

    async def _heartbeat(self, node_id: str, current_tasks: int = 0,
                        cpu_usage: float = None, memory_usage: float = None,
                        **kwargs) -> Dict[str, Any]:
        """节点心跳"""
        try:
            if node_id not in self.nodes:
                return {"status": "error", "error": "节点不存在"}

            node = self.nodes[node_id]

            # 更新节点状态
            node.last_heartbeat = time.time()
            node.current_tasks = current_tasks
            node.status = 'active'

            # 更新资源使用情况
            if cpu_usage is not None:
                node.cpu_usage = cpu_usage
            if memory_usage is not None:
                node.memory_usage = memory_usage

            # 更新系统资源信息（每10次心跳更新一次）
            if node.total_tasks_processed % 10 == 0:
                await self._update_node_resources(node)

            self.logger.debug(f"节点心跳: {node_id} (任务: {current_tasks})")

            return {
                "status": "success",
                "node_id": node_id,
                "timestamp": node.last_heartbeat,
                "next_heartbeat": node.last_heartbeat + node.heartbeat_interval
            }

        except Exception as e:
            self.logger.error(f"心跳处理失败: {e}")
            return {"status": "error", "error": f"心跳处理失败: {e}"}

    async def _get_node(self, node_id: str, **kwargs) -> Dict[str, Any]:
        """获取节点信息"""
        try:
            if node_id not in self.nodes:
                return {"status": "error", "error": "节点不存在"}

            node = self.nodes[node_id]

            return {
                "status": "success",
                "node": asdict(node)
            }

        except Exception as e:
            self.logger.error(f"获取节点信息失败: {e}")
            return {"status": "error", "error": f"获取节点信息失败: {e}"}

    async def _list_nodes(self, status: str = None, capability: str = None,
                         tag: str = None, **kwargs) -> Dict[str, Any]:
        """列出节点"""
        try:
            nodes = []

            for node in self.nodes.values():
                # 过滤条件
                if status and node.status != status:
                    continue
                if capability and capability not in node.capabilities:
                    continue
                if tag and tag not in node.tags:
                    continue

                nodes.append(asdict(node))

            return {
                "status": "success",
                "total_nodes": len(nodes),
                "nodes": nodes
            }

        except Exception as e:
            self.logger.error(f"列出节点失败: {e}")
            return {"status": "error", "error": f"列出节点失败: {e}"}

    async def _load_balance(self, task_type: str = 'crawl', preferred_tags: List[str] = None,
                          **kwargs) -> Dict[str, Any]:
        """负载均衡选择节点"""
        try:
            available_nodes = []

            # 筛选可用节点
            for node in self.nodes.values():
                if (node.status == 'active' and
                    task_type in node.capabilities and
                    node.current_tasks < node.max_concurrent_tasks):

                    # 检查标签偏好
                    if preferred_tags:
                        if not any(tag in node.tags for tag in preferred_tags):
                            continue

                    available_nodes.append(node)

            if not available_nodes:
                return {
                    "status": "error",
                    "error": "没有可用的节点"
                }

            # 根据策略选择节点
            strategy = self.config['load_balance_strategy']

            if strategy == 'random':
                selected_node = self._random_selection(available_nodes)
            elif strategy == 'round_robin':
                selected_node = self._round_robin_selection(available_nodes)
            elif strategy == 'least_loaded':
                selected_node = self._least_loaded_selection(available_nodes)
            elif strategy == 'weighted_round_robin':
                selected_node = self._weighted_round_robin_selection(available_nodes)
            else:
                selected_node = self._weighted_round_robin_selection(available_nodes)

            # 记录负载均衡历史
            self.load_balance_history.append({
                "timestamp": time.time(),
                "task_type": task_type,
                "selected_node": selected_node.node_id,
                "strategy": strategy,
                "available_nodes": len(available_nodes)
            })

            # 保持历史记录在合理范围内
            if len(self.load_balance_history) > 1000:
                self.load_balance_history = self.load_balance_history[-1000:]

            return {
                "status": "success",
                "selected_node": asdict(selected_node),
                "strategy": strategy,
                "available_nodes": len(available_nodes)
            }

        except Exception as e:
            self.logger.error(f"负载均衡失败: {e}")
            return {"status": "error", "error": f"负载均衡失败: {e}"}

    def _random_selection(self, nodes: List[NodeInfo]) -> NodeInfo:
        """随机选择"""
        return random.choice(nodes)

    def _round_robin_selection(self, nodes: List[NodeInfo]) -> NodeInfo:
        """轮询选择"""
        # 简单的轮询实现
        current_time = int(time.time())
        index = current_time % len(nodes)
        return nodes[index]

    def _least_loaded_selection(self, nodes: List[NodeInfo]) -> NodeInfo:
        """选择负载最小的节点"""
        return min(nodes, key=lambda x: x.current_tasks / max(x.max_concurrent_tasks, 1))

    def _weighted_round_robin_selection(self, nodes: List[NodeInfo]) -> NodeInfo:
        """加权轮询选择（基于性能指标）"""
        # 计算每个节点的权重
        node_weights = []
        for node in nodes:
            # 权重计算：成功率 * (1 - 负载率) * (1 / 平均响应时间)
            load_rate = node.current_tasks / max(node.max_concurrent_tasks, 1)
            response_factor = 1.0 / max(node.avg_response_time, 1.0)  # 避免除零

            weight = node.success_rate * (1 - load_rate) * response_factor
            node_weights.append((node, weight))

        # 按权重排序，选择权重最高的
        node_weights.sort(key=lambda x: x[1], reverse=True)
        return node_weights[0][0]

    async def _health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            current_time = time.time()
            checked_count = 0
            failed_count = 0

            for node_id, node in list(self.nodes.items()):
                checked_count += 1

                # 检查心跳超时
                if current_time - node.last_heartbeat > self.config['heartbeat_timeout']:
                    node.status = 'failed'
                    failed_count += 1
                    self.stats['failed_heartbeats'] += 1
                    self.logger.warning(f"节点心跳超时: {node_id}")

                # 检查负载过高
                elif node.current_tasks > node.max_concurrent_tasks * 1.5:
                    node.status = 'overloaded'
                    self.logger.warning(f"节点负载过高: {node_id}")

                # 检查资源使用率
                elif node.cpu_usage > 90 or node.memory_usage > 90:
                    node.status = 'overloaded'
                    self.logger.warning(f"节点资源使用过高: {node_id}")

            # 更新统计
            self._update_stats()

            return {
                "status": "success",
                "checked_count": checked_count,
                "failed_count": failed_count,
                "active_count": self.stats['active_nodes']
            }

        except Exception as e:
            self.logger.error(f"健康检查失败: {e}")
            return {"status": "error", "error": f"健康检查失败: {e}"}

    async def _scale_nodes(self, target_count: int, **kwargs) -> Dict[str, Any]:
        """节点扩容/缩容"""
        try:
            current_count = len(self.nodes)

            if target_count > current_count:
                # 扩容
                nodes_to_add = target_count - current_count
                added_count = 0

                for i in range(nodes_to_add):
                    result = await self._register_node(**kwargs)
                    if result['status'] == 'success':
                        added_count += 1

                return {
                    "status": "success",
                    "action": "scale_up",
                    "added_count": added_count,
                    "target_count": target_count
                }

            elif target_count < current_count:
                # 缩容
                nodes_to_remove = current_count - target_count
                removed_count = 0

                # 选择要移除的节点（优先移除负载低的）
                nodes_to_remove = sorted(
                    self.nodes.values(),
                    key=lambda x: x.current_tasks / max(x.max_concurrent_tasks, 1)
                )[:nodes_to_remove]

                for node in nodes_to_remove:
                    result = await self._unregister_node(node.node_id)
                    if result['status'] == 'success':
                        removed_count += 1

                return {
                    "status": "success",
                    "action": "scale_down",
                    "removed_count": removed_count,
                    "target_count": target_count
                }

            else:
                return {
                    "status": "success",
                    "action": "no_change",
                    "message": "节点数量已达到目标"
                }

        except Exception as e:
            self.logger.error(f"节点扩缩容失败: {e}")
            return {"status": "error", "error": f"节点扩缩容失败: {e}"}

    def _get_local_ip(self) -> str:
        """获取本机IP地址"""
        try:
            # 创建一个socket连接来获取本机IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    async def _update_node_resources(self, node: NodeInfo):
        """更新节点资源使用情况"""
        try:
            # CPU使用率
            node.cpu_usage = psutil.cpu_percent(interval=1)

            # 内存使用率
            memory = psutil.virtual_memory()
            node.memory_usage = memory.percent

            # 磁盘使用率
            disk = psutil.disk_usage('/')
            node.disk_usage = disk.percent

            # 网络带宽（简化为当前网络连接数）
            network = psutil.net_connections()
            node.network_bandwidth = len(network)

        except Exception as e:
            self.logger.warning(f"更新节点资源失败: {e}")

    def _update_stats(self):
        """更新统计信息"""
        total_nodes = len(self.nodes)
        active_nodes = len([n for n in self.nodes.values() if n.status == 'active'])
        total_capacity = sum(n.max_concurrent_tasks for n in self.nodes.values())
        used_capacity = sum(n.current_tasks for n in self.nodes.values())

        self.stats.update({
            'total_nodes': total_nodes,
            'active_nodes': active_nodes,
            'total_capacity': total_capacity,
            'used_capacity': used_capacity,
            'avg_load': used_capacity / max(total_capacity, 1)
        })

    async def start_background_tasks(self):
        """启动后台任务"""
        # 健康检查任务
        asyncio.create_task(self._background_health_check())

        # 节点清理任务
        asyncio.create_task(self._background_node_cleanup())

    async def _background_health_check(self):
        """后台健康检查"""
        while True:
            try:
                await self._health_check()
                await asyncio.sleep(self.config['health_check_interval'])
            except Exception as e:
                self.logger.error(f"后台健康检查出错: {e}")
                await asyncio.sleep(60)

    async def _background_node_cleanup(self):
        """后台节点清理"""
        while True:
            try:
                # 清理失败的节点
                failed_nodes = [node_id for node_id, node in self.nodes.items()
                              if node.status == 'failed']

                for node_id in failed_nodes:
                    if node_id in self.nodes:
                        del self.nodes[node_id]
                        self.logger.info(f"清理失败节点: {node_id}")

                # 更新统计
                self._update_stats()

                await asyncio.sleep(self.config['node_cleanup_interval'])
            except Exception as e:
                self.logger.error(f"后台节点清理出错: {e}")
                await asyncio.sleep(60)