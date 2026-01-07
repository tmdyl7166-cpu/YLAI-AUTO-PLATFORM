import time
import json
import requests
from prometheus_client import Counter, Histogram
from typing import Dict, Any, List
from .models import FuzzResult

DEFAULT_TIMEOUT = 10

# Prometheus metrics
FUZZ_REQUESTS = Counter('fuzz_requests_total', 'Total fuzz requests', ['method', 'status'])
FUZZ_ERRORS = Counter('fuzz_errors_total', 'Total fuzz errors', ['method'])
FUZZ_LATENCY = Histogram('fuzz_request_latency_ms', 'Fuzz request latency', buckets=(1,5,10,20,50,100,200,500,1000,2000,5000))

def _snapshot_response(resp: requests.Response) -> Dict[str, Any]:
    ct = resp.headers.get('Content-Type','')
    text = ''
    try:
        text = resp.text[:4096]
    except Exception:
        text = ''
    return {
        'status': resp.status_code,
        'headers': dict(resp.headers),
        'text': text,
        'content_type': ct,
        'length': len(resp.content or b'')
    }

def run_case(endpoint: str, method: str, params: Dict[str, Any], headers: Dict[str,str]|None=None, body: Any|None=None) -> FuzzResult:
    url = endpoint
    headers = headers or {}
    t0 = time.perf_counter()
    try:
        if method.upper() == 'GET':
            resp = requests.get(url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        elif method.upper() == 'POST':
            if isinstance(body, dict):
                resp = requests.post(url, json=body, headers=headers, timeout=DEFAULT_TIMEOUT)
            else:
                resp = requests.post(url, data=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        else:
            resp = requests.request(method, url, params=params, headers=headers, timeout=DEFAULT_TIMEOUT)
        elapsed = (time.perf_counter()-t0)*1000
        snap = _snapshot_response(resp)
        ok = 200 <= resp.status_code < 300
        FUZZ_REQUESTS.labels(method=method.upper(), status=str(resp.status_code)).inc()
        FUZZ_LATENCY.observe(elapsed)
        return FuzzResult(
            ok=ok,
            status=resp.status_code,
            elapsed_ms=elapsed,
            length=snap['length'],
            content_type=snap['content_type'],
            request_snapshot={'endpoint': endpoint, 'method': method, 'params': params, 'headers': headers},
            response_snapshot=snap,
            keywords=[],
            error=None
        )
    except Exception as e:
        elapsed = (time.perf_counter()-t0)*1000
        FUZZ_ERRORS.labels(method=method.upper()).inc()
        return FuzzResult(
            ok=False,
            status=-1,
            elapsed_ms=elapsed,
            length=0,
            content_type='',
            request_snapshot={'endpoint': endpoint, 'method': method, 'params': params, 'headers': headers},
            response_snapshot={},
            keywords=['exception'],
            error=str(e)
        )
