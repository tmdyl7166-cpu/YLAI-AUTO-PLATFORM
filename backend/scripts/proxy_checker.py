#!/usr/bin/env python3
"""
代理池系统 - 代理检测器模块
检测代理可用性和性能
"""

import asyncio
import time
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor
import aiohttp
import requests

from backend.core.base import BaseScript


class ProxyChecker(BaseScript):
    """代理检测器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 检测配置
        self.check_config = {
            'timeout': 10,  # 连接超时时间
            'max_workers': 50,  # 最大并发数
            'test_url': 'http://httpbin.org/ip',  # 测试URL
            'test_urls': [
                'http://httpbin.org/ip',
                'https://httpbin.org/ip',
                'http://ip-api.com/json',
                'https://api.ipify.org?format=json'
            ],
            'retry_count': 2,  # 重试次数
            'batch_size': 100  # 批处理大小
        }

        # 检测统计
        self.stats = {
            'total_checked': 0,
            'working_proxies': 0,
            'failed_proxies': 0,
            'avg_response_time': 0.0,
            'success_rate': 0.0
        }

    async def run(self, proxies: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """执行代理检测"""
        try:
            self.logger.info(f"开始检测 {len(proxies)} 个代理")

            # 预运行检查
            await self.pre_run()

            # 检测代理
            result = await self._check_proxies(proxies, **kwargs)

            # 后运行处理
            await self.post_run(result)

            return result

        except Exception as e:
            await self.on_error(e)
            return {
                "status": "error",
                "error": str(e),
                "stats": self.stats
            }

    async def _check_proxies(self, proxies: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """检测代理列表"""
        # 更新配置
        config = self.check_config.copy()
        config.update(kwargs)

        # 分批处理
        batch_size = config['batch_size']
        all_results = []

        for i in range(0, len(proxies), batch_size):
            batch = proxies[i:i + batch_size]
            self.logger.info(f"处理第 {i//batch_size + 1} 批代理 ({len(batch)} 个)")

            batch_results = await self._check_batch(batch, config)
            all_results.extend(batch_results)

            # 小延迟避免过载
            await asyncio.sleep(0.1)

        # 计算统计信息
        self._calculate_stats(all_results)

        # 按评分排序
        working_proxies = [p for p in all_results if p.get('working', False)]
        working_proxies.sort(key=lambda x: x.get('score', 0), reverse=True)

        result = {
            "status": "success",
            "timestamp": time.time(),
            "stats": self.stats,
            "total_proxies": len(proxies),
            "working_proxies": working_proxies,
            "failed_proxies": [p for p in all_results if not p.get('working', False)],
            "config": config
        }

        return result

    async def _check_batch(self, proxies: List[Dict[str, Any]], config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """检测一批代理"""
        semaphore = asyncio.Semaphore(config['max_workers'])

        async def check_single(proxy: Dict[str, Any]) -> Dict[str, Any]:
            async with semaphore:
                return await self._check_single_proxy(proxy, config)

        tasks = [check_single(proxy) for proxy in proxies]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                self.logger.warning(f"检测代理 {proxies[i].get('ip', 'unknown')} 出错: {result}")
                # 创建失败结果
                failed_result = proxies[i].copy()
                failed_result.update({
                    'working': False,
                    'error': str(result),
                    'response_time': -1,
                    'score': 0,
                    'checked_at': time.time()
                })
                processed_results.append(failed_result)
            else:
                processed_results.append(result)

        return processed_results

    async def _check_single_proxy(self, proxy: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """检测单个代理"""
        ip = proxy.get('ip')
        port = proxy.get('port')
        protocol = proxy.get('protocol', 'http')

        proxy_url = f"{protocol}://{ip}:{port}"
        result = proxy.copy()

        result.update({
            'working': False,
            'response_time': -1,
            'score': 0,
            'checked_at': time.time(),
            'error': None,
            'anonymity_level': 'unknown',
            'speed_rating': 'unknown'
        })

        # 尝试连接测试
        for attempt in range(config['retry_count'] + 1):
            try:
                start_time = time.time()

                # 使用aiohttp进行异步测试
                connector = aiohttp.TCPConnector(limit=1, ttl_dns_cache=30)
                timeout = aiohttp.ClientTimeout(total=config['timeout'])

                proxy_dict = {protocol: proxy_url}

                async with aiohttp.ClientSession(
                    connector=connector,
                    timeout=timeout
                ) as session:
                    async with session.get(
                        config['test_url'],
                        proxy=proxy_dict[protocol] if protocol in proxy_dict else None
                    ) as response:
                        response_time = time.time() - start_time

                        if response.status == 200:
                            # 解析响应
                            try:
                                data = await response.json()
                                real_ip = self._extract_ip_from_response(data, config['test_url'])
                            except:
                                real_ip = None

                            # 计算匿名等级
                            anonymity = self._calculate_anonymity(ip, real_ip)

                            # 计算评分
                            score = self._calculate_score(response_time, anonymity, response.status)

                            result.update({
                                'working': True,
                                'response_time': round(response_time, 3),
                                'real_ip': real_ip,
                                'anonymity_level': anonymity,
                                'speed_rating': self._get_speed_rating(response_time),
                                'score': score,
                                'last_success': time.time()
                            })

                            self.logger.debug(f"代理 {ip}:{port} 工作正常 - 响应时间: {response_time:.3f}s, 评分: {score}")
                            break
                        else:
                            result['error'] = f"HTTP {response.status}"

            except asyncio.TimeoutError:
                result['error'] = "timeout"
            except aiohttp.ClientError as e:
                result['error'] = f"connection_error: {str(e)}"
            except Exception as e:
                result['error'] = f"unknown_error: {str(e)}"

            # 重试延迟
            if attempt < config['retry_count']:
                await asyncio.sleep(0.5)

        return result

    def _extract_ip_from_response(self, data: Dict[str, Any], test_url: str) -> Optional[str]:
        """从响应中提取IP地址"""
        try:
            if 'origin' in data:
                # httpbin.org/ip
                return data['origin'].split(',')[0].strip()
            elif 'ip' in data:
                # ip-api.com/json
                return data['ip']
            elif 'query' in data:
                # api.ipify.org
                return data['query']
            else:
                return None
        except:
            return None

    def _calculate_anonymity(self, proxy_ip: str, real_ip: Optional[str]) -> str:
        """计算匿名等级"""
        if not real_ip:
            return 'unknown'

        if proxy_ip == real_ip:
            return 'transparent'  # 透明代理
        elif real_ip in ['unknown', None]:
            return 'unknown'
        else:
            return 'anonymous'  # 匿名代理

    def _calculate_score(self, response_time: float, anonymity: str, status_code: int) -> float:
        """计算代理评分"""
        score = 0.0

        # 响应时间评分 (0-50分)
        if response_time <= 1.0:
            score += 50
        elif response_time <= 3.0:
            score += 40
        elif response_time <= 5.0:
            score += 30
        elif response_time <= 10.0:
            score += 20
        else:
            score += 10

        # 匿名等级评分 (0-30分)
        if anonymity == 'anonymous':
            score += 30
        elif anonymity == 'transparent':
            score += 10

        # HTTP状态评分 (0-20分)
        if status_code == 200:
            score += 20
        elif status_code < 400:
            score += 15

        return round(score, 2)

    def _get_speed_rating(self, response_time: float) -> str:
        """获取速度评级"""
        if response_time <= 1.0:
            return 'excellent'
        elif response_time <= 3.0:
            return 'good'
        elif response_time <= 5.0:
            return 'fair'
        elif response_time <= 10.0:
            return 'poor'
        else:
            return 'very_slow'

    def _calculate_stats(self, results: List[Dict[str, Any]]):
        """计算统计信息"""
        total = len(results)
        working = len([r for r in results if r.get('working', False)])

        response_times = [r['response_time'] for r in results if r.get('working', False) and r['response_time'] > 0]

        self.stats.update({
            'total_checked': total,
            'working_proxies': working,
            'failed_proxies': total - working,
            'avg_response_time': round(sum(response_times) / len(response_times), 3) if response_times else 0.0,
            'success_rate': round(working / total * 100, 2) if total > 0 else 0.0
        })

    async def check_single_proxy_sync(self, proxy: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """同步检测单个代理（用于外部调用）"""
        config = self.check_config.copy()
        config.update(kwargs)
        return await self._check_single_proxy(proxy, config)

    async def check_proxies_continuously(self, proxies: List[Dict[str, Any]],
                                       interval: int = 300, **kwargs):
        """持续检测代理"""
        while True:
            try:
                self.logger.info("开始持续代理检测")
                result = await self.run(proxies, **kwargs)

                working_count = len(result['working_proxies'])
                self.logger.info(f"检测完成: {working_count}/{len(proxies)} 个代理工作正常")

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"持续检测出错: {e}")
                await asyncio.sleep(60)