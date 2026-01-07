#!/usr/bin/env python3
import os, asyncio, json, sys

API_TARGET = os.getenv('API_TARGET', 'http://127.0.0.1:8001')
URL = API_TARGET.replace('http', 'ws') + '/ws/monitor'
EXPECT_ACK = os.getenv('WS_EXPECT_ACK', '1') not in ('0', 'false', 'False')
TIMEOUT = float(os.getenv('WS_TIMEOUT', '2.0'))

async def main():
    print('[ws] trying', URL)
    try:
        import websockets
    except Exception as e:
        print('[ws] websockets not installed:', e)
        print('try: python -m pip install websockets')
        sys.exit(2)
    try:
        async with websockets.connect(URL, ping_interval=None) as ws:
            await ws.send(json.dumps({'type':'probe','ts':'local'}))
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=TIMEOUT)
                print('[ws] recv ok:', msg[:200])
                return 0
            except Exception:
                print('[ws] send ok; no recv')
                return 1 if EXPECT_ACK else 0
    except Exception as e:
        print('[ws] failed:', e)
        return 1

if __name__ == '__main__':
    rc = asyncio.run(main())
    sys.exit(rc)
