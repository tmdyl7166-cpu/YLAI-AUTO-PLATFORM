import requests
from typing import Dict, Any

class ShodanAPICollector:
    name = 'shodan'
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base = 'https://api.shodan.io/'

    def host(self, ip: str) -> Dict[str, Any]:
        url = self.base + f'shodan/host/{ip}'
        params = {'key': self.api_key}
        try:
            r = requests.get(url, params=params, timeout=10)
            j = r.json()
            return {'ok': r.status_code==200, 'status': r.status_code, 'data': j}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def resolve(self, hostname: str) -> Dict[str, Any]:
        url = self.base + 'dns/resolve'
        params = {'hostnames': hostname, 'key': self.api_key}
        try:
            r = requests.get(url, params=params, timeout=10)
            j = r.json()
            return {'ok': r.status_code==200, 'status': r.status_code, 'data': j}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def collect(self, query: Dict[str, Any]) -> Dict[str, Any]:
        ip = query.get('ip')
        hostname = query.get('hostname')
        if ip:
            res = self.host(ip)
        elif hostname:
            res = self.resolve(hostname)
        else:
            return {'source': self.name, 'ok': False, 'error': 'ip or hostname required'}
        return {'source': self.name, 'query': query, 'result': res}
