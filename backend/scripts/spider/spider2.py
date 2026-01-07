import time
from typing import Dict

def run(params: Dict) -> Dict:
    url = params.get("url", "https://example.org")
    for i in range(2):
        print(f"[Spider2] 抓取 {url} 第{i+1}次")
        time.sleep(1)
    return {"status": "success", "data": {"url": url, "content": "Spider2数据"}}
