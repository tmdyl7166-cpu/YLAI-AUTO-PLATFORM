"""
输出处理器插件
提供多种数据输出和处理能力
"""

import asyncio
import aiohttp
import json
import csv
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
from pathlib import Path
import logging

# 插件信息
PLUGIN_NAME = "输出处理器插件"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提供多种数据输出和处理能力"
PLUGIN_AUTHOR = "YLAI Team"

logger = logging.getLogger(__name__)

class OutputProcessor(ABC):
    """输出处理器抽象基类"""

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
    async def process_output(self, data: List[Dict[str, Any]], output_config: Dict[str, Any]) -> Dict[str, Any]:
        """处理输出"""
        pass

class FileOutputProcessor(OutputProcessor):
    """文件输出处理器"""

    async def process_output(self, data: List[Dict[str, Any]], output_config: Dict[str, Any]) -> Dict[str, Any]:
        """输出到文件"""
        file_path = output_config.get('file_path')
        format_type = output_config.get('format', 'json')
        append = output_config.get('append', False)

        if not file_path:
            raise ValueError("file_path is required for file output")

        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            mode = 'a' if append else 'w'
            encoding = output_config.get('encoding', 'utf-8')

            with open(file_path, mode, encoding=encoding) as f:
                if format_type == 'json':
                    if append and file_path.exists() and file_path.stat().st_size > 0:
                        # 追加到现有JSON数组
                        existing_data = json.load(open(file_path, 'r', encoding=encoding))
                        if isinstance(existing_data, list):
                            existing_data.extend(data)
                            json.dump(existing_data, f, ensure_ascii=False, indent=2)
                        else:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                    else:
                        json.dump(data, f, ensure_ascii=False, indent=2)

                elif format_type == 'csv':
                    if data:
                        fieldnames = list(data[0].keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        if not append or not file_path.exists():
                            writer.writeheader()
                        writer.writerows(data)

                elif format_type == 'txt':
                    for item in data:
                        if isinstance(item, dict):
                            f.write(json.dumps(item, ensure_ascii=False) + '\n')
                        else:
                            f.write(str(item) + '\n')

                else:
                    raise ValueError(f"Unsupported format: {format_type}")

            return {
                'success': True,
                'file_path': str(file_path),
                'records_processed': len(data),
                'format': format_type
            }

        except Exception as e:
            logger.error(f"File output error: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': str(file_path)
            }

class ApiOutputProcessor(OutputProcessor):
    """API输出处理器"""

    async def process_output(self, data: List[Dict[str, Any]], output_config: Dict[str, Any]) -> Dict[str, Any]:
        """输出到API"""
        url = output_config.get('url')
        method = output_config.get('method', 'POST')
        headers = output_config.get('headers', {})
        timeout = output_config.get('timeout', 30)

        if not url:
            raise ValueError("url is required for API output")

        try:
            if method.upper() == 'POST':
                async with self.session.post(url, json=data, headers=headers, timeout=timeout) as response:
                    result = await response.json()
            elif method.upper() == 'PUT':
                async with self.session.put(url, json=data, headers=headers, timeout=timeout) as response:
                    result = await response.json()
            else:
                raise ValueError(f"Unsupported method: {method}")

            return {
                'success': True,
                'url': url,
                'method': method,
                'status_code': response.status,
                'response': result,
                'records_sent': len(data)
            }

        except Exception as e:
            logger.error(f"API output error: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'method': method
            }

class DatabaseOutputProcessor(OutputProcessor):
    """数据库输出处理器"""

    async def process_output(self, data: List[Dict[str, Any]], output_config: Dict[str, Any]) -> Dict[str, Any]:
        """输出到数据库"""
        # 这里可以集成各种数据库，如SQLite, PostgreSQL, MongoDB等
        # 为简化实现，这里使用文件存储作为示例

        db_type = output_config.get('db_type', 'sqlite')
        table_name = output_config.get('table_name', 'data')
        file_path = output_config.get('file_path', f'{table_name}.db')

        try:
            if db_type == 'sqlite':
                import sqlite3
                import aiosqlite

                # 创建表结构（如果不存在）
                async with aiosqlite.connect(file_path) as db:
                    if data:
                        columns = list(data[0].keys())
                        create_table_sql = f"""
                        CREATE TABLE IF NOT EXISTS {table_name} (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            {', '.join([f'{col} TEXT' for col in columns])},
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                        """
                        await db.execute(create_table_sql)
                        await db.commit()

                        # 插入数据
                        placeholders = ', '.join(['?' for _ in columns])
                        columns_str = ', '.join(columns)
                        insert_sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"

                        for item in data:
                            values = [item.get(col, '') for col in columns]
                            await db.execute(insert_sql, values)

                        await db.commit()

            return {
                'success': True,
                'db_type': db_type,
                'table_name': table_name,
                'file_path': file_path,
                'records_inserted': len(data)
            }

        except Exception as e:
            logger.error(f"Database output error: {e}")
            return {
                'success': False,
                'error': str(e),
                'db_type': db_type,
                'table_name': table_name
            }

class OutputProcessorPlugin:
    """输出处理器插件主类"""

    def __init__(self):
        self.processors = {
            'file': FileOutputProcessor,
            'api': ApiOutputProcessor,
            'database': DatabaseOutputProcessor
        }

    def get_available_processors(self) -> List[str]:
        """获取可用输出处理器类型"""
        return list(self.processors.keys())

    def create_processor(self, processor_type: str, config: Dict[str, Any]) -> OutputProcessor:
        """创建输出处理器实例"""
        if processor_type not in self.processors:
            raise ValueError(f"Unknown output processor type: {processor_type}")

        return self.processors[processor_type](config)

    async def process_output(self, processor_type: str, config: Dict[str, Any], data: List[Dict[str, Any]], output_config: Dict[str, Any]) -> Dict[str, Any]:
        """使用指定处理器处理输出"""
        processor = self.create_processor(processor_type, config)
        async with processor:
            return await processor.process_output(data, output_config)

# 插件实例
plugin = OutputProcessorPlugin()

def get_available_processors():
    """获取可用输出处理器类型"""
def get_available_processors():
    """获取可用输出处理器类型"""
    return plugin.get_available_processors()

async def process_output(processor_type: str, config: Dict[str, Any], data: List[Dict[str, Any]], output_config: Dict[str, Any]):
    """处理输出"""
    return await plugin.process_output(processor_type, config, data, output_config)
