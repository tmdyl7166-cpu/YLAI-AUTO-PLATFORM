#!/usr/bin/env python3
"""
代理池系统 - 代理收集器模块
从各种来源收集代理IP
"""

import asyncio
import json
import re
import time
from typing import Dict, Any, List, Optional, Set
from urllib.parse import urlparse

import aiohttp
import requests
from bs4 import BeautifulSoup

from backend.core.base import BaseScript


class ProxyCollector(BaseScript):
    """代理收集器"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 代理来源配置
        self.sources = {
            'free_proxy_list': {
                'url': 'https://free-proxy-list.net/',
                'parser': self._parse_free_proxy_list
            },
            'proxy_scrape': {
                'url': 'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
                'parser': self._parse_proxy_scrape
            },
            'gimmeproxy': {
                'url': 'http://gimmeproxy.com/api/getProxy',
                'parser': self._parse_gimmeproxy
            },
            'proxylist': {
                'url': 'https://www.proxylist.me/',
                'parser': self._parse_proxylist_me
            },
            'proxy_list_download': {
                'url': 'https://www.proxy-list.download/api/v1/get?type=http',
                'parser': self._parse_proxy_list_download
            }
        }

        # 代理去重集合
        self.seen_proxies: Set[str] = set()

        # 收集统计
        self.stats = {
            'total_collected': 0,
            'unique_proxies': 0,
            'sources_processed': 0,
            'errors': 0
        }

    async def run(self, sources: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """执行代理收集"""
        try:
            self.logger.info("开始代理收集")

            # 预运行检查
            await self.pre_run()

            # 收集代理
            result = await self._collect_proxies(sources, **kwargs)

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

    async def _collect_proxies(self, sources: Optional[List[str]] = None, **kwargs) -> Dict[str, Any]:
        """收集代理"""
        # 确定要处理的来源
        if sources is None:
            sources = list(self.sources.keys())

        all_proxies = []
        self.stats = {
            'total_collected': 0,
            'unique_proxies': 0,
            'sources_processed': 0,
            'errors': 0
        }

        # 并发生集代理
        tasks = []
        for source_name in sources:
            if source_name in self.sources:
                task = self._collect_from_source(source_name)
                tasks.append(task)

        # 等待所有任务完成
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理结果
        for result in results:
            if isinstance(result, Exception):
                self.logger.error(f"收集任务出错: {result}")
                self.stats['errors'] += 1
                continue

            if result and 'proxies' in result:
                proxies = result['proxies']
                all_proxies.extend(proxies)
                self.stats['sources_processed'] += 1

        # 去重和验证
        unique_proxies = self._deduplicate_proxies(all_proxies)
        validated_proxies = await self._validate_proxies(unique_proxies)

        self.stats['total_collected'] = len(all_proxies)
        self.stats['unique_proxies'] = len(unique_proxies)

        result = {
            "status": "success",
            "timestamp": time.time(),
            "stats": self.stats,
            "proxies": validated_proxies,
            "sources": sources
        }

        return result

    async def _collect_from_source(self, source_name: str) -> Optional[Dict[str, Any]]:
        """从单个来源收集代理"""
        try:
            source_config = self.sources[source_name]
            url = source_config['url']
            parser = source_config['parser']

            self.logger.info(f"从 {source_name} 收集代理: {url}")

            # 发送请求
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as response:
                    if response.status != 200:
                        self.logger.warning(f"{source_name} 返回状态码: {response.status}")
                        return None

                    content = await response.text()

            # 解析代理
            proxies = await parser(content, source_name)

            self.logger.info(f"从 {source_name} 收集到 {len(proxies)} 个代理")

            return {
                "source": source_name,
                "proxies": proxies
            }

        except Exception as e:
            self.logger.error(f"从 {source_name} 收集代理失败: {e}")
            return None

    async def _parse_free_proxy_list(self, content: str, source: str) -> List[Dict[str, Any]]:
        """解析free-proxy-list.net"""
        proxies = []

        try:
            soup = BeautifulSoup(content, 'html.parser')
            table = soup.find('table', {'id': 'proxylisttable'})

            if not table:
                return proxies

            rows = table.find_all('tr')[1:]  # 跳过表头

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 8:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    country = cols[2].text.strip()
                    anonymity = cols[4].text.strip()
                    https = cols[6].text.strip().lower() == 'yes'

                    if ip and port:
                        proxy = {
                            "ip": ip,
                            "port": int(port),
                            "protocol": "https" if https else "http",
                            "country": country,
                            "anonymity": anonymity,
                            "source": source,
                            "collected_at": time.time()
                        }
                        proxies.append(proxy)

        except Exception as e:
            self.logger.error(f"解析 {source} 失败: {e}")

        return proxies

    async def _parse_proxy_scrape(self, content: str, source: str) -> List[Dict[str, Any]]:
        """解析proxyscrape API"""
        proxies = []

        try:
            lines = content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line:
                    ip, port = line.split(':', 1)
                    proxy = {
                        "ip": ip,
                        "port": int(port),
                        "protocol": "http",
                        "country": "unknown",
                        "anonymity": "unknown",
                        "source": source,
                        "collected_at": time.time()
                    }
                    proxies.append(proxy)

        except Exception as e:
            self.logger.error(f"解析 {source} 失败: {e}")

        return proxies

    async def _parse_gimmeproxy(self, content: str, source: str) -> List[Dict[str, Any]]:
        """解析gimmeproxy API"""
        proxies = []

        try:
            data = json.loads(content)
            if 'ip' in data and 'port' in data:
                proxy = {
                    "ip": data['ip'],
                    "port": int(data['port']),
                    "protocol": data.get('protocol', 'http'),
                    "country": data.get('country', 'unknown'),
                    "anonymity": data.get('anonymity', 'unknown'),
                    "source": source,
                    "collected_at": time.time()
                }
                proxies.append(proxy)

        except Exception as e:
            self.logger.error(f"解析 {source} 失败: {e}")

        return proxies

    async def _parse_proxylist_me(self, content: str, source: str) -> List[Dict[str, Any]]:
        """解析proxylist.me"""
        proxies = []

        try:
            soup = BeautifulSoup(content, 'html.parser')
            table = soup.find('table')

            if not table:
                return proxies

            rows = table.find_all('tr')[1:]  # 跳过表头

            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 6:
                    ip = cols[0].text.strip()
                    port = cols[1].text.strip()
                    country = cols[2].text.strip()
                    anonymity = cols[4].text.strip()

                    if ip and port:
                        proxy = {
                            "ip": ip,
                            "port": int(port),
                            "protocol": "http",
                            "country": country,
                            "anonymity": anonymity,
                            "source": source,
                            "collected_at": time.time()
                        }
                        proxies.append(proxy)

        except Exception as e:
            self.logger.error(f"解析 {source} 失败: {e}")

        return proxies

    async def _parse_proxy_list_download(self, content: str, source: str) -> List[Dict[str, Any]]:
        """解析proxy-list.download"""
        proxies = []

        try:
            lines = content.strip().split('\n')
            for line in lines:
                line = line.strip()
                if ':' in line:
                    ip, port = line.split(':', 1)
                    proxy = {
                        "ip": ip,
                        "port": int(port),
                        "protocol": "http",
                        "country": "unknown",
                        "anonymity": "unknown",
                        "source": source,
                        "collected_at": time.time()
                    }
                    proxies.append(proxy)

        except Exception as e:
            self.logger.error(f"解析 {source} 失败: {e}")

        return proxies

    def _deduplicate_proxies(self, proxies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """代理去重"""
        unique_proxies = []
        seen = set()

        for proxy in proxies:
            key = f"{proxy['ip']}:{proxy['port']}:{proxy['protocol']}"
            if key not in seen:
                seen.add(key)
                unique_proxies.append(proxy)

        return unique_proxies

    async def _validate_proxies(self, proxies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """初步验证代理格式"""
        validated = []

        for proxy in proxies:
            if self._is_valid_proxy(proxy):
                validated.append(proxy)

        return validated

    def _is_valid_proxy(self, proxy: Dict[str, Any]) -> bool:
        """验证代理格式"""
        try:
            # 检查必需字段
            if not all(key in proxy for key in ['ip', 'port', 'protocol']):
                return False

            # 验证IP格式
            ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
            if not re.match(ip_pattern, proxy['ip']):
                return False

            # 验证端口范围
            port = proxy['port']
            if not isinstance(port, int) or port < 1 or port > 65535:
                return False

            # 验证协议
            if proxy['protocol'] not in ['http', 'https', 'socks4', 'socks5']:
                return False

            return True

        except Exception:
            return False

    async def collect_periodically(self, interval: int = 3600, sources: Optional[List[str]] = None):
        """定期收集代理"""
        while True:
            try:
                self.logger.info(f"开始定期收集代理 (间隔: {interval}秒)")
                result = await self.run(sources)

                if result['status'] == 'success':
                    self.logger.info(f"收集完成: {result['stats']['unique_proxies']} 个唯一代理")

                await asyncio.sleep(interval)

            except Exception as e:
                self.logger.error(f"定期收集出错: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再试