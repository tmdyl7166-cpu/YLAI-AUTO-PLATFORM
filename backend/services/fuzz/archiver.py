import os
import json
from datetime import datetime
from typing import Dict, Any

BASE_DIR = os.path.join(os.path.dirname(__file__), '../../storage/anomalies')

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)


def archive(result: Dict[str, Any], tag: str = 'default') -> str:
    ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    out_dir = os.path.abspath(os.path.join(BASE_DIR, tag))
    ensure_dir(out_dir)
    fname = os.path.join(out_dir, f'anomaly_{ts}.json')
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return fname
