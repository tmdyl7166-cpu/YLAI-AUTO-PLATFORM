import asyncio
import os
from pathlib import Path
from typing import List
import aiohttp

LOG_DIR = Path('logs')
POLL_INTERVAL = float(os.getenv('LOG_COLLECT_INTERVAL', '5'))  # seconds
MAX_BYTES = int(os.getenv('LOG_COLLECT_MAX_BYTES', '10000'))
TARGET_URL = os.getenv('LOG_COLLECT_TARGET', 'http://127.0.0.1:8001/ai/optimize')

async def _read_tail(p: Path, max_bytes: int) -> str:
    try:
        data = p.read_bytes()
        if len(data) > max_bytes:
            data = data[-max_bytes:]
        return data.decode('utf-8', errors='ignore')
    except Exception:
        return ''

async def _post_error(session: aiohttp.ClientSession, text: str, source: str):
    try:
        payload = {"error_text": text, "context": {"source": source}}
        async with session.post(TARGET_URL, json=payload, timeout=10) as resp:
            await resp.text()
    except Exception:
        pass

async def collect_loop():
    await asyncio.sleep(2)
    async with aiohttp.ClientSession() as session:
        while True:
            files: List[Path] = []
            if LOG_DIR.exists():
                for f in LOG_DIR.glob('**/*.log'):
                    files.append(f)
            # also include backend logs path
            backend_logs = Path('backend') / 'logs'
            if backend_logs.exists():
                for f in backend_logs.glob('**/*.log'):
                    files.append(f)
            for f in files[:20]:  # cap per cycle
                tail = await _read_tail(f, MAX_BYTES)
                if tail:
                    await _post_error(session, tail, f"collector:{f}")
            await asyncio.sleep(POLL_INTERVAL)
