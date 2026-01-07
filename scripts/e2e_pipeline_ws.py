#!/usr/bin/env python3
"""
最小端到端验证：
1) POST /ai/pipeline 触发AI联动
2) 订阅 WS /ws/monitor 接收统一事件并打印关键字段

运行：
  . .venv/bin/activate 2>/dev/null || true
  python scripts/e2e_pipeline_ws.py --base http://127.0.0.1:8001 --ws ws://127.0.0.1:8001/ws/monitor --prompt "hello"
"""
import argparse
import asyncio
import json
import sys
from typing import Optional

import requests


async def ws_listen(url: str, duration: float = 10.0):
    try:
        import websockets
    except Exception:
        print("[WARN] websockets 未安装，跳过 WS 验证。pip install websockets")
        return
    print(f"[WS] 连接 {url}，持续 {duration}s...")
    try:
        async with websockets.connect(url) as ws:
            ws_rcv = asyncio.create_task(_recv_loop(ws))
            await asyncio.sleep(duration)
            ws_rcv.cancel()
    except Exception as e:
        print(f"[WS] 连接失败: {e}")


async def _recv_loop(ws):
    while True:
        try:
            msg = await ws.recv()
            try:
                evt = json.loads(msg)
                level = evt.get("level", "INFO")
                name = evt.get("name", "event")
                message = evt.get("message", "")
                layer = evt.get("layer")
                elapsed = evt.get("elapsed_ms")
                err = evt.get("error")
                print(f"[WS] {level} {name} | layer={layer} elapsed={elapsed} error={err} :: {message}")
            except Exception:
                print(f"[WS] {msg}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[WS] 接收错误: {e}")
            await asyncio.sleep(0.5)


def run_pipeline(base: str, prompt: str, extra: Optional[dict] = None):
    url = base.rstrip("/") + "/ai/pipeline"
    payload = {"prompt": prompt}
    if extra:
        payload.update(extra)
    print(f"[HTTP] POST {url} -> {json.dumps(payload, ensure_ascii=False)}")
    try:
        r = requests.post(url, json=payload, timeout=30)
        print(f"[HTTP] 状态码: {r.status_code}")
        try:
            print(json.dumps(r.json(), ensure_ascii=False, indent=2))
        except Exception:
            print(r.text)
    except Exception as e:
        print(f"[HTTP] 请求失败: {e}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8001")
    ap.add_argument("--ws", default="ws://127.0.0.1:8001/ws/monitor")
    ap.add_argument("--prompt", default="hello")
    ap.add_argument("--duration", type=float, default=8.0)
    args = ap.parse_args()

    run_pipeline(args.base, args.prompt)
    try:
        asyncio.run(ws_listen(args.ws, duration=args.duration))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    sys.exit(main())
