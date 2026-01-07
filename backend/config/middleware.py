"""FastAPI middleware for metrics collection and request logging."""
import logging
import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from backend.config.metrics import (
    request_count, 
    request_duration, 
    active_connections,
    errors_total
)

logger = logging.getLogger(__name__)


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect Prometheus metrics for HTTP requests."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip metrics for /metrics endpoint itself
        if request.url.path == "/metrics":
            return await call_next(request)
        
        method = request.method
        endpoint = request.url.path
        
        start_time = time.time()
        active_connections.inc()
        
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as exc:
            status = 500
            errors_total.labels(
                error_type=type(exc).__name__,
                endpoint=endpoint
            ).inc()
            active_connections.dec()
            raise
        finally:
            duration = time.time() - start_time
            request_count.labels(
                method=method,
                endpoint=endpoint,
                status=status
            ).inc()
            request_duration.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            active_connections.dec()
        
        return response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Middleware to add request context (request_id, etc.) to logs."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Generate or get request_id
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Store in state for access by handlers
        request.state.request_id = request_id
        request.state.user_id = request.headers.get("X-User-ID")
        
        # Add to logs
        logger.info(
            f"Incoming request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client": request.client.host if request.client else None,
            }
        )
        
        response = await call_next(request)
        
        # Add request_id to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
