"""Prometheus metrics collection and exposition for the application."""
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, REGISTRY
import time
from functools import wraps

# Define custom metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=REGISTRY
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=REGISTRY
)

active_connections = Gauge(
    'http_active_connections',
    'Number of active connections',
    registry=REGISTRY
)

cache_hits = Counter(
    'cache_hits_total',
    'Total cache hits',
    ['cache_name'],
    registry=REGISTRY
)

cache_misses = Counter(
    'cache_misses_total',
    'Total cache misses',
    ['cache_name'],
    registry=REGISTRY
)

db_connections = Gauge(
    'database_connections_active',
    'Number of active database connections',
    registry=REGISTRY
)

task_queue_size = Gauge(
    'task_queue_size',
    'Size of task queue',
    registry=REGISTRY
)

errors_total = Counter(
    'errors_total',
    'Total errors encountered',
    ['error_type', 'endpoint'],
    registry=REGISTRY
)


def track_metrics(endpoint: str):
    """Decorator to track metrics for an endpoint."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            method = "ASYNC"
            start = time.time()
            try:
                active_connections.inc()
                result = await func(*args, **kwargs)
                request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status=200
                ).inc()
                return result
            except Exception as e:
                request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status=500
                ).inc()
                errors_total.labels(
                    error_type=type(e).__name__,
                    endpoint=endpoint
                ).inc()
                raise
            finally:
                duration = time.time() - start
                request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                active_connections.dec()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            method = "SYNC"
            start = time.time()
            try:
                active_connections.inc()
                result = func(*args, **kwargs)
                request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status=200
                ).inc()
                return result
            except Exception as e:
                request_count.labels(
                    method=method,
                    endpoint=endpoint,
                    status=500
                ).inc()
                errors_total.labels(
                    error_type=type(e).__name__,
                    endpoint=endpoint
                ).inc()
                raise
            finally:
                duration = time.time() - start
                request_duration.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(duration)
                active_connections.dec()

        # Return async or sync wrapper based on function
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    return decorator
