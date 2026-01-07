import time
from typing import Dict

def run(params: Dict) -> Dict:
    url = params.get("url", "https://example.com")
    for i in range(3):
        print(f"[Spider1] 抓取 {url} 第{i+1}次")
        time.sleep(1)
    return {"status": "success", "data": {"url": url, "content": "Spider1数据"}}
