"""
数据源插件
提供多种数据源的统一接口和数据获取能力
"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import json
from pathlib import Path

# 插件信息
PLUGIN_NAME = "数据源插件"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提供多种数据源的统一接口和数据获取能力"
PLUGIN_AUTHOR = "YLAI Team"

class DataSource(ABC):
    """数据源抽象基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @abstractmethod
    async def fetch_data(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """获取数据"""
        pass

    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        """获取数据模式"""
        pass

class WebDataSource(DataSource):
    """网页数据源"""

    async def fetch_data(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从网页获取数据"""
        url = query.get('url')
        if not url:
            raise ValueError("URL is required for web data source")

        headers = query.get('headers', {})
        timeout = query.get('timeout', 30)

        try:
            async with self.session.get(url, headers=headers, timeout=timeout) as response:
                if response.status == 200:
                    content = await response.text()
                    return [{
                        'url': url,
                        'content': content,
                        'status': response.status,
                        'headers': dict(response.headers),
                        'timestamp': asyncio.get_event_loop().time()
                    }]
                else:
                    return [{
                        'url': url,
                        'error': f'HTTP {response.status}',
                        'status': response.status,
                        'timestamp': asyncio.get_event_loop().time()
                    }]
        except Exception as e:
            return [{
                'url': url,
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }]

    async def get_schema(self) -> Dict[str, Any]:
        """获取网页数据模式"""
        return {
            'type': 'web',
            'fields': {
                'url': {'type': 'string', 'required': True},
                'headers': {'type': 'object', 'required': False},
                'timeout': {'type': 'integer', 'default': 30}
            }
        }

class ApiDataSource(DataSource):
    """API数据源"""

    async def fetch_data(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从API获取数据"""
        url = query.get('url')
        method = query.get('method', 'GET')
        headers = query.get('headers', {})
        params = query.get('params', {})
        data = query.get('data', {})
        timeout = query.get('timeout', 30)

        try:
            if method.upper() == 'GET':
                async with self.session.get(url, headers=headers, params=params, timeout=timeout) as response:
                    result = await response.json()
            elif method.upper() == 'POST':
                async with self.session.post(url, headers=headers, params=params, json=data, timeout=timeout) as response:
                    result = await response.json()
            else:
                raise ValueError(f"Unsupported method: {method}")

            return [{
                'url': url,
                'method': method,
                'data': result,
                'status': response.status,
                'timestamp': asyncio.get_event_loop().time()
            }]

        except Exception as e:
            return [{
                'url': url,
                'method': method,
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }]

    async def get_schema(self) -> Dict[str, Any]:
        """获取API数据模式"""
        return {
            'type': 'api',
            'fields': {
                'url': {'type': 'string', 'required': True},
                'method': {'type': 'string', 'enum': ['GET', 'POST'], 'default': 'GET'},
                'headers': {'type': 'object', 'required': False},
                'params': {'type': 'object', 'required': False},
                'data': {'type': 'object', 'required': False},
                'timeout': {'type': 'integer', 'default': 30}
            }
        }

class FileDataSource(DataSource):
    """文件数据源"""

    async def fetch_data(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从文件获取数据"""
        file_path = query.get('file_path')
        if not file_path:
            raise ValueError("file_path is required for file data source")

        file_path = Path(file_path)
        if not file_path.exists():
            return [{
                'file_path': str(file_path),
                'error': 'File not found',
                'timestamp': asyncio.get_event_loop().time()
            }]

        try:
            if file_path.suffix.lower() == '.json':
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            elif file_path.suffix.lower() in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = {'content': f.read()}
            else:
                return [{
                    'file_path': str(file_path),
                    'error': f'Unsupported file type: {file_path.suffix}',
                    'timestamp': asyncio.get_event_loop().time()
                }]

            return [{
                'file_path': str(file_path),
                'data': data,
                'size': file_path.stat().st_size,
                'timestamp': asyncio.get_event_loop().time()
            }]

        except Exception as e:
            return [{
                'file_path': str(file_path),
                'error': str(e),
                'timestamp': asyncio.get_event_loop().time()
            }]

    async def get_schema(self) -> Dict[str, Any]:
        """获取文件数据模式"""
        return {
            'type': 'file',
            'fields': {
                'file_path': {'type': 'string', 'required': True}
            }
        }

class DataSourcePlugin:
    """数据源插件主类"""

    def __init__(self):
        self.sources = {
            'web': WebDataSource,
            'api': ApiDataSource,
            'file': FileDataSource
        }

    def get_available_sources(self) -> List[str]:
        """获取可用数据源类型"""
        return list(self.sources.keys())

    def create_source(self, source_type: str, config: Dict[str, Any]) -> DataSource:
        """创建数据源实例"""
        if source_type not in self.sources:
            raise ValueError(f"Unknown data source type: {source_type}")

        return self.sources[source_type](config)

    async def fetch_from_source(self, source_type: str, config: Dict[str, Any], query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """从指定数据源获取数据"""
        source = self.create_source(source_type, config)
        async with source:
            return await source.fetch_data(query)

    async def get_source_schema(self, source_type: str) -> Dict[str, Any]:
        """获取数据源模式"""
        if source_type not in self.sources:
            raise ValueError(f"Unknown data source type: {source_type}")

        # 创建临时实例获取模式
        source = self.sources[source_type]({})
        return await source.get_schema()

# 插件实例
plugin = DataSourcePlugin()

def get_available_sources():
    """获取可用数据源类型"""
    return plugin.get_available_sources()

def get_available_sources():
    """获取可用数据源类型"""
    return plugin.get_available_sources()

async def fetch_data(source_type: str, config: Dict[str, Any], query: Dict[str, Any]):
    """获取数据"""
    return await plugin.fetch_from_source(source_type, config, query)

async def get_schema(source_type: str):
    """获取数据源模式"""
    return await plugin.get_source_schema(source_type)
