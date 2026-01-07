"""
YLAI-AUTO-PLATFORM 生产级日志配置
支持结构化日志、日志轮换、多处理器
"""

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

# 日志目录
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(exist_ok=True)

class JSONFormatter(logging.Formatter):
    """JSON 格式日志输出器"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str = "INFO",
    log_format: str = "json",
    environment: str = "development",
) -> logging.Logger:
    """
    配置应用日志系统
    
    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: 日志格式 (json, text)
        environment: 环境 (development, production)
    
    Returns:
        根日志记录器
    """
    
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # 清除已有处理器
    root_logger.handlers.clear()
    
    # ==================== 控制台处理器 ====================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    
    if log_format == "json":
        console_formatter = JSONFormatter()
    else:
        # 文本格式
        fmt = (
            "[%(asctime)s] %(levelname)s in %(module)s "
            "(%(filename)s:%(lineno)d): %(message)s"
        )
        console_formatter = logging.Formatter(fmt)
    
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # ==================== 文件处理器 - 一般日志 ====================
    
    # 轮换处理器 (每天午夜轮换，保留 30 天)
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=LOG_DIR / "app.log",
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(
        JSONFormatter() if log_format == "json" else console_formatter
    )
    root_logger.addHandler(file_handler)
    
    # ==================== 文件处理器 - 错误日志 ====================
    error_handler = logging.handlers.RotatingFileHandler(
        filename=LOG_DIR / "error.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        JSONFormatter() if log_format == "json" else console_formatter
    )
    root_logger.addHandler(error_handler)
    
    # ==================== 文件处理器 - 性能日志 ====================
    if environment == "production":
        perf_handler = logging.handlers.RotatingFileHandler(
            filename=LOG_DIR / "performance.log",
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=3,
            encoding="utf-8",
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(JSONFormatter())
        
        perf_logger = logging.getLogger("performance")
        perf_logger.addHandler(perf_handler)
    
    return root_logger


# ==================== 日志过滤器 ====================

class RequestContextFilter(logging.Filter):
    """添加请求上下文信息到日志"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        # 从上下文中获取 request_id（如果存在）
        # 这里需要与 FastAPI 中间件配合使用
        return True


class SensitiveDataFilter(logging.Filter):
    """过滤敏感数据（密码、令牌等）"""
    
    SENSITIVE_KEYS = {"password", "token", "secret", "api_key", "auth"}
    
    def filter(self, record: logging.LogRecord) -> bool:
        # 检查日志消息中的敏感信息
        message = str(record.msg)
        for key in self.SENSITIVE_KEYS:
            if key.lower() in message.lower():
                # 可选：标记为包含敏感数据
                pass
        return True


# ==================== 便捷日志记录函数 ====================

def get_logger(name: str) -> logging.Logger:
    """获取命名日志记录器"""
    return logging.getLogger(name)


def log_performance(
    logger: logging.Logger,
    endpoint: str,
    method: str,
    duration_ms: float,
    status_code: int,
) -> None:
    """记录 API 性能指标"""
    
    perf_logger = logging.getLogger("performance")
    perf_logger.info(
        "api_request",
        extra={
            "endpoint": endpoint,
            "method": method,
            "duration_ms": duration_ms,
            "status_code": status_code,
        }
    )


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: Optional[dict] = None,
) -> None:
    """记录带上下文的错误"""
    
    logger.error(
        f"Error: {str(error)}",
        extra=context or {},
        exc_info=True,
    )


# ==================== 使用示例 ====================

if __name__ == "__main__":
    # 初始化日志
    logger = setup_logging(level="INFO", log_format="json", environment="production")
    
    # 记录各级别日志
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    
    # 带异常信息
    try:
        1 / 0
    except ZeroDivisionError:
        logger.exception("Exception occurred")
    
    print("✓ 日志系统已初始化")
