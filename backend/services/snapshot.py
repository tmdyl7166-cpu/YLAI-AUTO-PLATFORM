import os
import json
import hashlib
from pathlib import Path
from datetime import datetime

def _hash_str(s: str) -> str:
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:16]

class SnapshotStore:
    def __init__(self, base_dir: str | Path | None = None):
        base = base_dir or os.getenv("SNAPSHOT_DIR", "./logs/snapshots")
        self.base = Path(base).resolve()
        self.base.mkdir(parents=True, exist_ok=True)

    def save(self, kind: str, payload: dict) -> dict:
        ts = datetime.utcnow().strftime('%Y%m%dT%H%M%S.%fZ')
        ver = payload.get('script_version') or ''
        ver_hash = _hash_str(ver) if ver else ''
        snap_id = f"{kind}-{ts}-{ver_hash}" if ver_hash else f"{kind}-{ts}"
        data = {
            "id": snap_id,
            "kind": kind,
            "ts": ts,
            "payload": payload,
        }
        fp = self.base / f"{snap_id}.json"
        with fp.open('w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data

    def list(self, limit: int = 50) -> list[dict]:
        items = []
        for p in sorted(self.base.glob('*.json'), reverse=True):
            try:
                with p.open('r', encoding='utf-8') as f:
                    items.append(json.load(f))
            except Exception:
                continue
            if len(items) >= limit:
                break
        return items

    def get(self, snap_id: str) -> dict | None:
        fp = self.base / f"{snap_id}.json"
        if not fp.exists():
            return None
        try:
            with fp.open('r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

store = SnapshotStore()
