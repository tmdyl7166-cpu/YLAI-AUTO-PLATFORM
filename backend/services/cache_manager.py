import redis
import json
from typing import Any, Optional, Dict
import asyncio
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis = redis.from_url(redis_url)
        self.default_ttl = 3600  # 1小时

    async def get(self, key: str) -> Optional[Any]:
        """异步获取缓存"""
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"Cache get error: {e}")
        return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """异步设置缓存"""
        try:
            ttl = ttl or self.default_ttl
            data = json.dumps(value, ensure_ascii=False)
            return self.redis.setex(key, ttl, data)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return self.redis.delete(key) > 0
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return self.redis.exists(key) > 0
        except Exception as e:
            print(f"Cache exists error: {e}")
            return False

    def get_sync(self, key: str) -> Optional[Any]:
        """同步获取缓存"""
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data.decode('utf-8'))
        except Exception as e:
            print(f"Cache get error: {e}")
        return None

    def set_sync(self, key: str, value: Any, ttl: int = None) -> bool:
        """同步设置缓存"""
        try:
            ttl = ttl or self.default_ttl
            data = json.dumps(value, ensure_ascii=False)
            return self.redis.setex(key, ttl, data)
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

# 全局缓存管理器实例
cache_manager = CacheManager()