"""
缓存服务模块
提供Redis缓存和内存缓存功能
"""
import json
import hashlib
from typing import Any, Optional, Union
import redis
import yaml
from pathlib import Path


class CacheService:
    """缓存服务类"""

    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.config = self._load_config()

        # 初始化Redis连接
        if self.config.get('redis', {}).get('enabled', True):
            self._init_redis()

    async def initialize(self):
        """初始化缓存服务"""
        # 确保Redis连接可用
        if self.redis_client:
            try:
                self.redis_client.ping()
            except Exception:
                self.redis_client = None
        return True

    def _load_config(self) -> dict:
        """加载性能配置"""
        config_path = Path(__file__).parent.parent / "config" / "performance.yaml"
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            # 默认配置
            return {
                'redis': {
                    'host': '127.0.0.1',
                    'port': 6379,
                    'db': 0,
                    'enabled': False
                },
                'cache': {
                    'default_ttl': 3600
                }
            }

    def _init_redis(self):
        """初始化Redis连接"""
        redis_config = self.config.get('redis', {})
        try:
            self.redis_client = redis.Redis(
                host=redis_config.get('host', '127.0.0.1'),
                port=redis_config.get('port', 6379),
                db=redis_config.get('db', 0),
                password=redis_config.get('password'),
                decode_responses=True
            )
            # 测试连接
            self.redis_client.ping()
        except Exception as e:
            print(f"Redis连接失败，使用内存缓存: {e}")
            self.redis_client = None

    def _make_key(self, key: str) -> str:
        """生成缓存键"""
        prefix = self.config.get('redis', {}).get('key_prefix', 'ylai:')
        return f"{prefix}{key}"

    def _serialize_value(self, value: Any) -> str:
        """序列化值"""
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return str(value)

    def _deserialize_value(self, value: str) -> Any:
        """反序列化值"""
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        cache_key = self._make_key(key)

        # 优先从Redis获取
        if self.redis_client:
            try:
                value = self.redis_client.get(cache_key)
                if value:
                    return self._deserialize_value(value)
            except Exception:
                pass

        # 从内存缓存获取
        return self.memory_cache.get(cache_key)

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存值"""
        cache_key = self._make_key(key)
        serialized_value = self._serialize_value(value)

        if ttl is None:
            ttl = self.config.get('cache', {}).get('default_ttl', 3600)

        # 设置到Redis
        if self.redis_client:
            try:
                return bool(self.redis_client.setex(cache_key, ttl, serialized_value))
            except Exception:
                pass

        # 设置到内存缓存
        self.memory_cache[cache_key] = value
        return True

    def delete(self, key: str) -> bool:
        """删除缓存"""
        cache_key = self._make_key(key)

        # 从Redis删除
        if self.redis_client:
            try:
                self.redis_client.delete(cache_key)
            except Exception:
                pass

        # 从内存缓存删除
        if cache_key in self.memory_cache:
            del self.memory_cache[cache_key]

        return True

    def exists(self, key: str) -> bool:
        """检查缓存是否存在"""
        cache_key = self._make_key(key)

        # 检查Redis
        if self.redis_client:
            try:
                return bool(self.redis_client.exists(cache_key))
            except Exception:
                pass

        # 检查内存缓存
        return cache_key in self.memory_cache

    def clear(self) -> bool:
        """清空所有缓存"""
        try:
            # 清空Redis
            if self.redis_client:
                prefix = self.config.get('redis', {}).get('key_prefix', 'ylai:')
                keys = self.redis_client.keys(f"{prefix}*")
                if keys:
                    self.redis_client.delete(*keys)

            # 清空内存缓存
            self.memory_cache.clear()
            return True
        except Exception:
            return False

    def get_or_set(self, key: str, func, ttl: Optional[int] = None):
        """获取缓存，如果不存在则设置"""
        value = self.get(key)
        if value is not None:
            return value

        value = func()
        self.set(key, value, ttl)
        return value

    def close(self):
        """关闭缓存服务"""
        try:
            if self.redis_client:
                self.redis_client.close()
            self.memory_cache.clear()
        except Exception:
            pass


# 全局缓存服务实例
cache_service = CacheService()