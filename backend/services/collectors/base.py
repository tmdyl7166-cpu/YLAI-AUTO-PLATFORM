from typing import Dict, Any

class Collector:
    name: str = 'base'
    def collect(self, query: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

class RateLimiter:
    def __init__(self, rate_per_sec: float = 1.0):
        self.rate = rate_per_sec

    def wait(self):
        # TODO: implement token bucket
        pass
