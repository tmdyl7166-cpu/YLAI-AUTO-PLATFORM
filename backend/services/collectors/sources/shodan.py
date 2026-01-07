from ..base import Collector
from typing import Dict, Any

class ShodanCollector(Collector):
    name = 'shodan'
    def __init__(self, api_key: str):
        self.api_key = api_key

    def collect(self, query: Dict[str, Any]) -> Dict[str, Any]:
        # Placeholder: integrate shodan client later
        return { 'source': self.name, 'query': query, 'data': [] }
