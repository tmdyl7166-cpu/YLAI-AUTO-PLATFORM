import time
from typing import Dict

def run(params: Dict) -> Dict:
    """
    DAG 调用接口
    params: 节点传入参数，例如 {"url":"https://example.com"}
    返回值: {"status":"success","data":...}
    """
    url = params.get("url", "https://example.com")
    print(f"[{url}] 爬虫任务开始")
    
    # 模拟爬取过程
    for i in range(3):
        print(f"[{url}] 抓取第 {i+1} 次数据...")
        time.sleep(1)  # 模拟网络请求
        # 这里可通过 WebSocket 推送状态
        # send_ws_status(node_id, status="running", elapsed=i+1)
    
    print(f"[{url}] 爬虫任务完成")
    return {"status": "success", "data": {"url": url, "content": "爬取示例内容"}}
