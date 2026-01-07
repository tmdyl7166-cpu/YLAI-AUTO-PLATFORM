"""
YLAI-AUTO-PLATFORM 性能和安全配置
包含缓存策略、速率限制、CORS、输入验证等
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis
from functools import wraps
import time
from typing import Optional, Callable, Any
from datetime import timedelta

# ==================== 缓存配置 ====================

class CacheConfig:
    """缓存策略配置"""
    
    # Redis 连接
    REDIS_URL = "redis://127.0.0.1:6379/0"
    REDIS_SOCKET_TIMEOUT = 5
    REDIS_SOCKET_CONNECT_TIMEOUT = 5
    
    # 缓存过期时间
    CACHE_TTL = {
        "default": 3600,           # 1 小时
        "short": 300,              # 5 分钟
        "medium": 1800,            # 30 分钟
        "long": 86400,             # 1 天
        "user": 7200,              # 2 小时
        "task": 1800,              # 30 分钟
        "health": 60,              # 1 分钟
    }
    
    # 缓存策略
    CACHE_STRATEGIES = {
        "/api/health": "health",           # 快速过期
        "/api/tasks": "medium",            # 中等过期
        "/api/users": "long",              # 长期缓存
        "/api/config": "long",             # 配置级缓存
    }


def cache(expire: Optional[int] = None, key_prefix: str = ""):
    """
    缓存装饰器
    
    Args:
        expire: 过期时间（秒）
        key_prefix: 缓存键前缀
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            redis_client = redis.from_url(CacheConfig.REDIS_URL)
            
            # 生成缓存键
            cache_key = f"{key_prefix or func.__name__}:{args}:{kwargs}"
            
            # 尝试从缓存获取
            cached = redis_client.get(cache_key)
            if cached:
                return eval(cached)
            
            # 执行函数
            result = await func(*args, **kwargs)
            
            # 存储到缓存
            ttl = expire or CacheConfig.CACHE_TTL.get("default", 3600)
            redis_client.setex(cache_key, ttl, str(result))
            
            return result
        
        return wrapper
    
    return decorator


# ==================== 速率限制配置 ====================

class RateLimitConfig:
    """API 速率限制配置"""
    
    # 全局限制
    GLOBAL_LIMIT = "10000/hour"
    
    # 用户限制
    USER_LIMITS = {
        "default": "1000/minute",
        "read": "2000/minute",
        "write": "500/minute",
        "auth": "10/minute",
    }
    
    # IP 限制
    IP_LIMITS = {
        "default": "100/second",
        "strict": "10/second",      # 登录失败、异常行为
    }
    
    # 端点特定限制
    ENDPOINT_LIMITS = {
        "/api/auth/login": "5/minute",
        "/api/auth/register": "3/minute",
        "/api/tasks": "100/minute",
        "/api/tasks/run": "50/minute",
    }


def get_rate_limiter():
    """获取速率限制器"""
    return Limiter(key_func=get_remote_address)


# ==================== CORS 配置 ====================

class CORSConfig:
    """CORS 跨域资源共享配置"""
    
    # 允许的源
    ALLOWED_ORIGINS = [
        "http://localhost:3000",
        "http://127.0.0.1",
        "http://ylai.local",
        "https://ylai.local",
        "https://www.ylai.com",
    ]
    
    # 允许的方法
    ALLOWED_METHODS = ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]
    
    # 允许的请求头
    ALLOWED_HEADERS = [
        "Content-Type",
        "Authorization",
        "Accept",
        "Accept-Language",
        "Content-Language",
        "X-Request-ID",
    ]
    
    # 暴露的响应头
    EXPOSE_HEADERS = [
        "X-Request-ID",
        "X-Response-Time",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ]
    
    # 预检请求缓存时间
    MAX_AGE = 600


def setup_cors(app: FastAPI) -> None:
    """配置 CORS 中间件"""
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORSConfig.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=CORSConfig.ALLOWED_METHODS,
        allow_headers=CORSConfig.ALLOWED_HEADERS,
        expose_headers=CORSConfig.EXPOSE_HEADERS,
        max_age=CORSConfig.MAX_AGE,
    )


# ==================== 安全头配置 ====================

class SecurityHeadersConfig:
    """HTTP 安全头配置"""
    
    HEADERS = {
        # XSS 保护
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "X-XSS-Protection": "1; mode=block",
        
        # CSP (内容安全策略)
        "Content-Security-Policy": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' https:; "
        ),
        
        # HSTS (强制 HTTPS)
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        
        # 引用政策
        "Referrer-Policy": "strict-origin-when-cross-origin",
        
        # 功能政策
        "Permissions-Policy": (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
        ),
    }


# ==================== 输入验证配置 ====================

class ValidationConfig:
    """输入数据验证配置"""
    
    # 字符串字段限制
    STRING_MAX_LENGTH = 10000
    STRING_MIN_LENGTH = 1
    
    # 数字范围
    INT_MAX = 2147483647
    INT_MIN = -2147483648
    
    # 文件上传限制
    MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
    ALLOWED_FILE_TYPES = [
        "application/json",
        "text/csv",
        "application/pdf",
    ]
    
    # SQL 注入防护关键字
    SQL_INJECTION_KEYWORDS = [
        "UNION", "SELECT", "INSERT", "UPDATE", "DELETE",
        "DROP", "CREATE", "ALTER", "EXEC", "SCRIPT",
    ]
    
    @staticmethod
    def validate_input(value: str) -> bool:
        """验证输入是否包含 SQL 注入"""
        return not any(
            keyword in value.upper()
            for keyword in ValidationConfig.SQL_INJECTION_KEYWORDS
        )


# ==================== 加密配置 ====================

class EncryptionConfig:
    """数据加密配置"""
    
    # JWT 配置
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION = timedelta(hours=1)
    JWT_REFRESH_EXPIRATION = timedelta(days=7)
    
    # 密码哈希
    PASSWORD_HASH_ALGORITHM = "bcrypt"
    PASSWORD_HASH_ROUNDS = 12
    
    # 敏感字段加密
    ENCRYPTED_FIELDS = {
        "users.password",
        "users.phone",
        "tasks.api_key",
        "config.secret_key",
    }


# ==================== 监控中间件 ====================

class PerformanceMiddleware:
    """性能监控中间件"""
    
    def __init__(self, app: FastAPI) -> None:
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                headers = list(message.get("headers", []))
                
                # 添加性能头
                headers.append(
                    (b"x-response-time", f"{duration:.3f}s".encode())
                )
                headers.append(
                    (b"x-process-time", f"{duration * 1000:.1f}ms".encode())
                )
                
                message["headers"] = headers
            
            await send(message)
        
        await self.app(scope, receive, send_wrapper)


# ==================== 设置函数 ====================

def setup_performance_and_security(app: FastAPI) -> None:
    """配置性能和安全中间件"""
    
    # 1. 启用 Gzip 压缩
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # 2. 添加性能监控
    app.add_middleware(PerformanceMiddleware)
    
    # 3. 配置 CORS
    setup_cors(app)
    
    # 4. 添加安全头
    @app.middleware("http")
    async def add_security_headers(request, call_next):
        response = await call_next(request)
        for header, value in SecurityHeadersConfig.HEADERS.items():
            response.headers[header] = value
        return response
    
    # 5. 速率限制
    limiter = get_rate_limiter()
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request, exc):
        return {
            "code": 4029,
            "message": "Too many requests",
            "error": str(exc),
        }


# ==================== 使用示例 ====================

if __name__ == "__main__":
    app = FastAPI(title="YLAI-AUTO-PLATFORM", version="1.0.0")
    
    # 配置性能和安全
    setup_performance_and_security(app)
    
    # 缓存示例
    @cache(expire=CacheConfig.CACHE_TTL["medium"], key_prefix="tasks")
    async def get_tasks():
        return [{"id": 1, "name": "Task 1"}]
    
    print("✓ 性能和安全配置已应用")
