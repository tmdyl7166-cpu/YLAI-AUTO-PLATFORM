"""
数据处理器插件
提供数据清洗、转换、分析和处理能力
"""

import asyncio
import re
import json
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from datetime import datetime
import hashlib
import logging

# 插件信息
PLUGIN_NAME = "数据处理器插件"
PLUGIN_VERSION = "1.0.0"
PLUGIN_DESCRIPTION = "提供数据清洗、转换、分析和处理能力"
PLUGIN_AUTHOR = "YLAI Team"

logger = logging.getLogger(__name__)

class DataHandler(ABC):
    """数据处理器抽象基类"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def process_data(self, data: List[Dict[str, Any]], handler_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """处理数据"""
        pass

class FilterHandler(DataHandler):
    """数据过滤处理器"""

    async def process_data(self, data: List[Dict[str, Any]], handler_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """过滤数据"""
        conditions = handler_config.get('conditions', [])

        if not conditions:
            return data

        filtered_data = []
        for item in data:
            match = True
            for condition in conditions:
                field = condition.get('field')
                operator = condition.get('operator', 'eq')
                value = condition.get('value')

                if field not in item:
                    match = False
                    break

                item_value = item[field]

                if operator == 'eq':
                    if item_value != value:
                        match = False
                        break
                elif operator == 'ne':
                    if item_value == value:
                        match = False
                        break
                elif operator == 'gt':
                    if not (isinstance(item_value, (int, float)) and item_value > value):
                        match = False
                        break
                elif operator == 'lt':
                    if not (isinstance(item_value, (int, float)) and item_value < value):
                        match = False
                        break
                elif operator == 'contains':
                    if value not in str(item_value):
                        match = False
                        break
                elif operator == 'regex':
                    if not re.search(value, str(item_value)):
                        match = False
                        break

            if match:
                filtered_data.append(item)

        return filtered_data

class TransformHandler(DataHandler):
    """数据转换处理器"""

    async def process_data(self, data: List[Dict[str, Any]], handler_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """转换数据"""
        transformations = handler_config.get('transformations', [])

        if not transformations:
            return data

        transformed_data = []
        for item in data:
            new_item = item.copy()

            for transform in transformations:
                action = transform.get('action')
                field = transform.get('field')
                target_field = transform.get('target_field', field)

                if action == 'rename':
                    if field in new_item:
                        new_item[target_field] = new_item.pop(field)

                elif action == 'add':
                    value = transform.get('value', '')
                    new_item[target_field] = value

                elif action == 'remove':
                    if field in new_item:
                        del new_item[field]

                elif action == 'lowercase':
                    if field in new_item and isinstance(new_item[field], str):
                        new_item[target_field] = new_item[field].lower()

                elif action == 'uppercase':
                    if field in new_item and isinstance(new_item[field], str):
                        new_item[target_field] = new_item[field].upper()

                elif action == 'trim':
                    if field in new_item and isinstance(new_item[field], str):
                        new_item[target_field] = new_item[field].strip()

                elif action == 'hash':
                    if field in new_item:
                        hash_value = hashlib.md5(str(new_item[field]).encode()).hexdigest()
                        new_item[target_field] = hash_value

                elif action == 'timestamp':
                    if field in new_item:
                        try:
                            dt = datetime.fromisoformat(new_item[field].replace('Z', '+00:00'))
                            new_item[target_field] = dt.timestamp()
                        except:
                            new_item[target_field] = new_item[field]

            transformed_data.append(new_item)

        return transformed_data

class AggregateHandler(DataHandler):
    """数据聚合处理器"""

    async def process_data(self, data: List[Dict[str, Any]], handler_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """聚合数据"""
        group_by = handler_config.get('group_by', [])
        aggregations = handler_config.get('aggregations', [])

        if not group_by or not aggregations:
            return data

        # 分组数据
        groups = {}
        for item in data:
            key_parts = []
            for field in group_by:
                key_parts.append(str(item.get(field, '')))
            key = '|'.join(key_parts)

            if key not in groups:
                groups[key] = []
            groups[key].append(item)

        # 聚合每组
        aggregated_data = []
        for key, group_items in groups.items():
            aggregated_item = {}

            # 设置分组字段
            key_parts = key.split('|')
            for i, field in enumerate(group_by):
                aggregated_item[field] = key_parts[i] if i < len(key_parts) else ''

            # 执行聚合
            for agg in aggregations:
                field = agg.get('field')
                func = agg.get('function', 'count')
                target_field = agg.get('target_field', f'{field}_{func}')

                values = [item.get(field) for item in group_items if field in item]

                if func == 'count':
                    aggregated_item[target_field] = len(values)
                elif func == 'sum':
                    try:
                        aggregated_item[target_field] = sum(float(v) for v in values if v is not None)
                    except:
                        aggregated_item[target_field] = 0
                elif func == 'avg':
                    try:
                        numeric_values = [float(v) for v in values if v is not None]
                        aggregated_item[target_field] = sum(numeric_values) / len(numeric_values) if numeric_values else 0
                    except:
                        aggregated_item[target_field] = 0
                elif func == 'min':
                    try:
                        numeric_values = [float(v) for v in values if v is not None]
                        aggregated_item[target_field] = min(numeric_values) if numeric_values else 0
                    except:
                        aggregated_item[target_field] = 0
                elif func == 'max':
                    try:
                        numeric_values = [float(v) for v in values if v is not None]
                        aggregated_item[target_field] = max(numeric_values) if numeric_values else 0
                    except:
                        aggregated_item[target_field] = 0
                elif func == 'first':
                    aggregated_item[target_field] = values[0] if values else None
                elif func == 'last':
                    aggregated_item[target_field] = values[-1] if values else None

            aggregated_data.append(aggregated_item)

        return aggregated_data

class ValidationHandler(DataHandler):
    """数据验证处理器"""

    async def process_data(self, data: List[Dict[str, Any]], handler_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """验证数据"""
        rules = handler_config.get('rules', [])
        action = handler_config.get('action', 'filter')  # filter, mark, or remove

        if not rules:
            return data

        processed_data = []
        for item in data:
            valid = True
            validation_errors = []

            for rule in rules:
                field = rule.get('field')
                rule_type = rule.get('type')
                required = rule.get('required', False)

                if field not in item:
                    if required:
                        valid = False
                        validation_errors.append(f"Missing required field: {field}")
                    continue

                value = item[field]

                if rule_type == 'string':
                    min_length = rule.get('min_length')
                    max_length = rule.get('max_length')
                    pattern = rule.get('pattern')

                    if not isinstance(value, str):
                        valid = False
                        validation_errors.append(f"Field {field} must be string")
                        continue

                    if min_length and len(value) < min_length:
                        valid = False
                        validation_errors.append(f"Field {field} too short (min: {min_length})")

                    if max_length and len(value) > max_length:
                        valid = False
                        validation_errors.append(f"Field {field} too long (max: {max_length})")

                    if pattern and not re.match(pattern, value):
                        valid = False
                        validation_errors.append(f"Field {field} does not match pattern")

                elif rule_type == 'number':
                    min_value = rule.get('min_value')
                    max_value = rule.get('max_value')

                    try:
                        num_value = float(value)
                        if min_value is not None and num_value < min_value:
                            valid = False
                            validation_errors.append(f"Field {field} too small (min: {min_value})")
                        if max_value is not None and num_value > max_value:
                            valid = False
                            validation_errors.append(f"Field {field} too large (max: {max_value})")
                    except:
                        valid = False
                        validation_errors.append(f"Field {field} must be number")

                elif rule_type == 'email':
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, str(value)):
                        valid = False
                        validation_errors.append(f"Field {field} is not a valid email")

            if action == 'filter':
                if valid:
                    processed_data.append(item)
            elif action == 'mark':
                item_copy = item.copy()
                item_copy['_valid'] = valid
                if not valid:
                    item_copy['_validation_errors'] = validation_errors
                processed_data.append(item_copy)
            elif action == 'remove':
                if valid:
                    processed_data.append(item)

        return processed_data

class DataHandlerPlugin:
    """数据处理器插件主类"""

    def __init__(self):
        self.handlers = {
            'filter': FilterHandler,
            'transform': TransformHandler,
            'aggregate': AggregateHandler,
            'validate': ValidationHandler
        }

    def get_available_handlers(self) -> List[str]:
        """获取可用数据处理器类型"""
        return list(self.handlers.keys())

    def create_handler(self, handler_type: str, config: Dict[str, Any]) -> DataHandler:
        """创建数据处理器实例"""
        if handler_type not in self.handlers:
            raise ValueError(f"Unknown data handler type: {handler_type}")

        return self.handlers[handler_type](config)

    async def process_data(self, handler_type: str, config: Dict[str, Any], data: List[Dict[str, Any]], handler_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """使用指定处理器处理数据"""
        handler = self.create_handler(handler_type, config)
        return await handler.process_data(data, handler_config)

# 插件实例
plugin = DataHandlerPlugin()

def get_available_handlers():
    """获取可用数据处理器类型"""
    return plugin.get_available_handlers()

async def process_data(handler_type: str, config: Dict[str, Any], data: List[Dict[str, Any]], handler_config: Dict[str, Any]):
    """处理数据"""
    return await plugin.process_data(handler_type, config, data, handler_config)
