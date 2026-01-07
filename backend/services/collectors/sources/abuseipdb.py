import requests
from typing import Dict, Any

class AbuseIPDBCollector:
    name = 'abuseipdb'
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base = 'https://api.abuseipdb.com/api/v2/'

    def report_check(self, ip: str) -> Dict[str, Any]:
        url = self.base + 'check'
        params = {'ipAddress': ip, 'maxAgeInDays': 90}
        headers = {'Key': self.api_key, 'Accept': 'application/json'}
        try:
            r = requests.get(url, params=params, headers=headers, timeout=10)
            j = r.json()
            return {'ok': r.status_code==200, 'status': r.status_code, 'data': j}
        except Exception as e:
            return {'ok': False, 'error': str(e)}

    def collect(self, query: Dict[str, Any]) -> Dict[str, Any]:
        ip = query.get('ip')
        if not ip:
            return {'ok': False, 'error': 'ip required'}
        res = self.report_check(ip)
        return {'source': self.name, 'query': query, 'result': res}
