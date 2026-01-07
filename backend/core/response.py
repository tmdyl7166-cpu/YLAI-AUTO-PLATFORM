"""
统一的 API 响应格式定义

所有 API 端点应使用此格式返回数据，确保前端能统一处理响应

使用示例:
    from backend.core.response import APIResponse, SuccessResponse, ErrorResponse
    
    @app.get("/api/health")
    def health():
        return SuccessResponse(data={"status": "healthy"})
    
    try:
        # 业务逻辑
    except ValueError as e:
        return ErrorResponse(code=1001, message=str(e))
"""

from datetime import datetime
from typing import Any, Optional, Dict
from enum import IntEnum
from pydantic import BaseModel, Field


class ErrorCode(IntEnum):
    """标准错误码"""
    # 成功 (0)
    SUCCESS = 0

    # 客户端错误 (1xxx)
    BAD_REQUEST = 1000
    INVALID_PARAMETER = 1001
    UNAUTHORIZED = 1002
    FORBIDDEN = 1003
    NOT_FOUND = 1004
    CONFLICT = 1005

    # 服务端错误 (2xxx)
    INTERNAL_ERROR = 2000
    SERVICE_UNAVAILABLE = 2001
    TIMEOUT = 2002
    DATABASE_ERROR = 2003

    # 业务错误 (3xxx)
    BUSINESS_ERROR = 3000
    TASK_ERROR = 3001
    PIPELINE_ERROR = 3002
    AI_ERROR = 3003


class APIResponse(BaseModel):
    """
    标准 API 响应格式

    所有 API 端点应返回此格式，确保：
    1. 前端能统一处理响应
    2. 错误信息清晰
    3. 数据与元数据分离
    4. 易于版本管理
    """
    code: int = Field(default=0, description="响应状态码（0=成功，其他=失败）")
    message: str = Field(default="OK", description="响应消息")
    data: Optional[Any] = Field(default=None, description="响应数据")
    timestamp: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
        description="响应时间戳（ISO 8601 格式）"
    )
    request_id: Optional[str] = Field(default=None, description="请求 ID（用于追踪）")
    
    # 分页信息（可选）
    pagination: Optional[Dict[str, int]] = Field(
        default=None,
        description="分页信息（包含 total、page、page_size）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "code": 0,
                "message": "OK",
                "data": {"status": "healthy"},
                "timestamp": "2026-01-07T10:00:00.000000",
                "request_id": "req-12345"
            }
        }


def SuccessResponse(
    data: Any = None,
    message: str = "OK",
    code: int = ErrorCode.SUCCESS,
    request_id: Optional[str] = None,
    pagination: Optional[Dict[str, int]] = None,
) -> APIResponse:
    """
    成功响应快捷函数
    
    使用示例:
        return SuccessResponse(data={"user_id": 123})
    """
    return APIResponse(
        code=code,
        message=message,
        data=data,
        request_id=request_id,
        pagination=pagination,
    )


def ErrorResponse(
    code: int = ErrorCode.INTERNAL_ERROR,
    message: str = "Internal Server Error",
    data: Any = None,
    request_id: Optional[str] = None,
) -> APIResponse:
    """
    错误响应快捷函数
    
    使用示例:
        return ErrorResponse(
            code=ErrorCode.INVALID_PARAMETER,
            message="Invalid user ID"
        )
    """
    return APIResponse(
        code=code,
        message=message,
        data=data,
        request_id=request_id,
    )


def PaginatedResponse(
    data: list,
    total: int,
    page: int = 1,
    page_size: int = 20,
    message: str = "OK",
) -> APIResponse:
    """
    分页响应快捷函数
    
    使用示例:
        return PaginatedResponse(
            data=users,
            total=100,
            page=1,
            page_size=20
        )
    """
    return APIResponse(
        code=ErrorCode.SUCCESS,
        message=message,
        data=data,
        pagination={
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": (total + page_size - 1) // page_size,
        },
    )
