#!/usr/bin/env python3
"""
代理池系统 - 集成模块
将代理池与爬虫脚本集成
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

from backend.scripts.proxy_collector import ProxyCollector
from backend.scripts.proxy_checker import ProxyChecker
from backend.scripts.proxy_manager import ProxyManager, RotationStrategy
from backend.core.base import BaseScript


class ProxyPoolIntegration(BaseScript):
    """代理池集成器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 组件实例
        self.collector = ProxyCollector()
        self.checker = ProxyChecker()
        self.manager = ProxyManager()

        # 集成配置
        self.config = {
            'auto_collect': True,      # 自动收集代理
            'auto_check': True,        # 自动检测代理
            'collect_interval': 3600,  # 收集间隔(秒)
            'check_interval': 300,     # 检测间隔(秒)
            'min_pool_size': 10,       # 最小池大小
            'max_pool_size': 1000,     # 最大池大小
            'rotation_strategy': RotationStrategy.SCORE_BASED,
            'geo_filter': None,        # 地理位置过滤
        }

        # 运行状态
        self.running = False
        self.tasks = []

    async def run(self, action: str, **kwargs) -> Dict[str, Any]:
        """执行集成操作"""
        try:
            self.logger.info(f"执行代理池集成操作: {action}")

            # 预运行检查
            await self.pre_run()

            # 执行操作
            if action == 'initialize':
                result = await self._initialize_pool(**kwargs)
            elif action == 'get_proxy':
                result = await self._get_proxy_for_crawler(**kwargs)
            elif action == 'report_usage':
                result = await self._report_proxy_usage(**kwargs)
            elif action == 'start_background':
                result = await self._start_background_tasks()
            elif action == 'stop_background':
                result = await self._stop_background_tasks()
            elif action == 'get_status':
                result = await self._get_pool_status()
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

    async def _initialize_pool(self, **kwargs) -> Dict[str, Any]:
        """初始化代理池"""
        self.logger.info("初始化代理池")

        # 更新配置
        self.config.update(kwargs)

        # 设置管理器策略
        if self.config['geo_filter']:
            self.manager.set_geo_filter(self.config['geo_filter'])
        self.manager.set_rotation_strategy(self.config['rotation_strategy'])

        # 初始收集代理
        if self.config['auto_collect']:
            collect_result = await self.collector.run()
            if collect_result['status'] == 'success':
                proxies = collect_result['proxies']
                self.logger.info(f"收集到 {len(proxies)} 个代理")

                # 检测代理
                if self.config['auto_check'] and proxies:
                    check_result = await self.checker.run(proxies)
                    if check_result['status'] == 'success':
                        working_proxies = check_result['working_proxies']
                        self.logger.info(f"检测出 {len(working_proxies)} 个工作代理")

                        # 添加到管理器
                        add_result = await self.manager.run('add_proxies', proxies=working_proxies)
                        self.logger.info(f"添加到代理池: {add_result.get('added_count', 0)} 个")

        return {
            "status": "success",
            "message": "代理池初始化完成",
            "config": self.config
        }

    async def _get_proxy_for_crawler(self, **kwargs) -> Dict[str, Any]:
        """为爬虫获取代理"""
        strategy = kwargs.get('strategy', self.config['rotation_strategy'].value)

        # 检查池大小
        pool_status = await self.manager.run('get_stats')
        active_count = pool_status.get('stats', {}).get('active_proxies', 0)

        if active_count < self.config['min_pool_size']:
            self.logger.warning(f"代理池大小不足 ({active_count} < {self.config['min_pool_size']})，尝试补充")

            # 触发代理收集
            if self.config['auto_collect']:
                collect_result = await self.collector.run()
                if collect_result['status'] == 'success':
                    proxies = collect_result['proxies']
                    if proxies:
                        # 快速检测
                        check_result = await self.checker.run(proxies[:50])  # 只检测前50个
                        if check_result['status'] == 'success':
                            working_proxies = check_result['working_proxies']
                            if working_proxies:
                                await self.manager.run('add_proxies', proxies=working_proxies)

        # 获取代理
        proxy_result = await self.manager.run('get_proxy', strategy=strategy)

        if proxy_result['status'] == 'success':
            proxy_data = proxy_result['proxy']
            proxy_key = proxy_result['proxy_key']

            return {
                "status": "success",
                "proxy": {
                    "http": f"http://{proxy_data['ip']}:{proxy_data['port']}",
                    "https": f"http://{proxy_data['ip']}:{proxy_data['port']}"
                },
                "proxy_info": proxy_data,
                "proxy_key": proxy_key,
                "strategy": strategy
            }
        else:
            return proxy_result

    async def _report_proxy_usage(self, proxy_key: str, success: bool,
                                response_time: float = 0, **kwargs) -> Dict[str, Any]:
        """报告代理使用结果"""
        result = await self.manager.run('report_result',
                                      proxy_key=proxy_key,
                                      success=success,
                                      response_time=response_time)

        if not success:
            self.logger.warning(f"代理 {proxy_key} 使用失败")

        return result

    async def _start_background_tasks(self) -> Dict[str, Any]:
        """启动后台任务"""
        if self.running:
            return {"status": "error", "error": "后台任务已在运行"}

        self.running = True
        self.tasks = []

        # 代理收集任务
        if self.config['auto_collect']:
            collect_task = asyncio.create_task(self._background_collect())
            self.tasks.append(collect_task)

        # 代理检测任务
        if self.config['auto_check']:
            check_task = asyncio.create_task(self._background_check())
            self.tasks.append(check_task)

        # 代理清理任务
        cleanup_task = asyncio.create_task(self._background_cleanup())
        self.tasks.append(cleanup_task)

        self.logger.info("代理池后台任务已启动")

        return {
            "status": "success",
            "message": "后台任务已启动",
            "tasks_count": len(self.tasks)
        }

    async def _stop_background_tasks(self) -> Dict[str, Any]:
        """停止后台任务"""
        if not self.running:
            return {"status": "success", "message": "后台任务未运行"}

        self.running = False

        # 取消所有任务
        for task in self.tasks:
            task.cancel()

        # 等待任务完成
        try:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        except asyncio.CancelledError:
            pass

        self.tasks = []
        self.logger.info("代理池后台任务已停止")

        return {
            "status": "success",
            "message": "后台任务已停止"
        }

    async def _background_collect(self):
        """后台代理收集"""
        while self.running:
            try:
                self.logger.debug("执行后台代理收集")

                collect_result = await self.collector.run()
                if collect_result['status'] == 'success':
                    proxies = collect_result['proxies']
                    if proxies:
                        # 检测新代理
                        check_result = await self.checker.run(proxies)
                        if check_result['status'] == 'success':
                            working_proxies = check_result['working_proxies']
                            if working_proxies:
                                await self.manager.run('add_proxies', proxies=working_proxies)
                                self.logger.info(f"后台收集: 添加 {len(working_proxies)} 个工作代理")

                # 等待下次收集
                await asyncio.sleep(self.config['collect_interval'])

            except Exception as e:
                self.logger.error(f"后台收集出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟

    async def _background_check(self):
        """后台代理检测"""
        while self.running:
            try:
                self.logger.debug("执行后台代理检测")

                # 获取当前代理池
                pool_snapshot = await self.manager.get_proxy_pool_snapshot()
                current_proxies = [p for p in pool_snapshot['proxies'] if p['status'] == 'active']

                if current_proxies:
                    # 转换为检测格式
                    proxies_to_check = []
                    for p in current_proxies[:50]:  # 每次最多检测50个
                        proxy_data = {
                            'ip': p['ip'],
                            'port': p['port'],
                            'protocol': p.get('protocol', 'http'),
                            'source': 'pool_check'
                        }
                        proxies_to_check.append(proxy_data)

                    # 执行检测
                    check_result = await self.checker.run(proxies_to_check)
                    if check_result['status'] == 'success':
                        working_proxies = check_result['working_proxies']
                        self.logger.debug(f"后台检测: {len(working_proxies)}/{len(proxies_to_check)} 个代理工作正常")

                # 等待下次检测
                await asyncio.sleep(self.config['check_interval'])

            except Exception as e:
                self.logger.error(f"后台检测出错: {e}")
                await asyncio.sleep(60)

    async def _background_cleanup(self):
        """后台代理清理"""
        while self.running:
            try:
                self.logger.debug("执行后台代理清理")

                # 执行健康检查
                await self.manager.run('health_check')

                # 执行清理
                cleanup_result = await self.manager.run('cleanup')
                if cleanup_result['status'] == 'success':
                    removed = cleanup_result.get('removed_count', 0)
                    if removed > 0:
                        self.logger.info(f"后台清理: 移除 {removed} 个过期代理")

                # 每小时执行一次
                await asyncio.sleep(3600)

            except Exception as e:
                self.logger.error(f"后台清理出错: {e}")
                await asyncio.sleep(60)

    async def _get_pool_status(self) -> Dict[str, Any]:
        """获取代理池状态"""
        manager_stats = await self.manager.run('get_stats')
        pool_snapshot = await self.manager.get_proxy_pool_snapshot()

        return {
            "status": "success",
            "running": self.running,
            "background_tasks": len(self.tasks),
            "stats": manager_stats.get('stats', {}),
            "pool_size": pool_snapshot['total_proxies'],
            "config": self.config
        }

    @asynccontextmanager
    async def get_proxy_session(self, **kwargs):
        """获取带代理的会话上下文管理器"""
        proxy_result = await self._get_proxy_for_crawler(**kwargs)

        if proxy_result['status'] != 'success':
            raise RuntimeError(f"无法获取代理: {proxy_result.get('error', 'unknown')}")

        proxy_info = proxy_result['proxy']
        proxy_key = proxy_result['proxy_key']

        try:
            yield proxy_info
            # 使用成功
            await self._report_proxy_usage(proxy_key, True, 0)
        except Exception as e:
            # 使用失败
            await self._report_proxy_usage(proxy_key, False, 0)
            raise e

    async def get_proxy_for_requests(self, **kwargs) -> Optional[Dict[str, str]]:
        """为requests库获取代理格式"""
        proxy_result = await self._get_proxy_for_crawler(**kwargs)

        if proxy_result['status'] == 'success':
            return proxy_result['proxy']
        else:
            self.logger.warning(f"获取代理失败: {proxy_result.get('error')}")
            return None

    async def get_multiple_proxies(self, count: int, **kwargs) -> List[Dict[str, Any]]:
        """获取多个代理"""
        proxies = []

        for _ in range(count):
            proxy_result = await self._get_proxy_for_crawler(**kwargs)
            if proxy_result['status'] == 'success':
                proxies.append(proxy_result)
            else:
                break

        return proxies