try:
    from prometheus_client import Counter, Histogram, Gauge  # type: ignore
except Exception:  # no prometheus_client installed
    class _Noop:
        def __init__(self, *_, **__):
            pass
        def labels(self, *_, **__):
            return self
        def inc(self, *_):
            pass
        def observe(self, *_):
            pass
        def set(self, *_):
            pass
    Counter = Histogram = Gauge = _Noop  # type: ignore

# API level metrics
API_REQUESTS_TOTAL = Counter("api_requests_total", "Total API requests", ["path", "method", "status"])  # type: ignore

# Pipeline metrics
PIPELINE_RUNS_TOTAL = Counter("pipeline_runs_total", "Total pipeline run requests")  # type: ignore
PIPELINE_RUNS_OVERALL = Counter(
    "pipeline_runs_overall_total", "Overall pipeline runs by mode and status", ["mode", "status"]
)  # type: ignore
PIPELINE_NODE_SECONDS = Histogram(
    "pipeline_node_seconds", "Pipeline node execution seconds", ["mode", "script"],
    buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10, 30, 60)
)  # type: ignore
PIPELINE_NODE_FAILURES = Counter(
    "pipeline_node_failures_total", "Pipeline node failures", ["mode", "script"]
)  # type: ignore

# Node retries
PIPELINE_NODE_RETRIES = Counter(
    "pipeline_node_retries_total", "Pipeline node retry attempts", ["mode", "script"]
)  # type: ignore

# AI call latency
AI_REQUEST_SECONDS = Histogram("ai_request_seconds", "AI request duration seconds", buckets=(0.05, 0.1, 0.25, 0.5, 1, 2, 5, 10))  # type: ignore

# WebSocket connections
WS_CONNECTIONS = Gauge("ws_connections", "Current active websocket connections", ["endpoint"])  # type: ignore

# Scheduler metrics
SCHEDULER_QUEUE_DEPTH = Gauge("scheduler_queue_depth", "Number of queued pipeline tasks")  # type: ignore
SCHEDULER_RUNNING = Gauge("scheduler_running_pipelines", "Number of running pipeline tasks")  # type: ignore
SCHEDULER_TASKS_TOTAL = Counter("scheduler_tasks_total", "Scheduler task state transitions", ["status"])  # type: ignore
