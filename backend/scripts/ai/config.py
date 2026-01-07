from pathlib import Path
import os
import yaml

_DEFAULTS = {
    "watch_dir": "./backend",
    "rule_path": "backend/scripts/ai/rules.json",
    "poll_interval": 5,
    "auto_fix": True,
    "ollama_url": os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434/api/generate"),
    "ollama_model": os.environ.get("OLLAMA_MODEL", "gpt-oss:20b"),
    "max_workers": 4,
    "backup_dir": "logs/backup",
}


def _load_yaml_config(path: Path) -> dict:
    try:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                return {}
            return data
    except Exception:
        return {}


def get_config() -> dict:
    cfg_path = Path(os.environ.get("AI_CONFIG_PATH", "config.yaml"))
    user_cfg = _load_yaml_config(cfg_path)
    merged = dict(_DEFAULTS)
    for k, v in user_cfg.items():
        if isinstance(v, dict) and isinstance(merged.get(k), dict):
            mv = dict(merged[k])
            mv.update(v)
            merged[k] = mv
        else:
            merged[k] = v
    merged["WATCH_DIR"] = Path(merged["watch_dir"])  
    merged["RULE_PATH"] = Path(merged["rule_path"])  
    merged["BACKUP_DIR"] = Path(merged["backup_dir"]) 
    return merged

_cfg = get_config()
WATCH_DIR = _cfg["WATCH_DIR"]
WATCH_DIRS = [WATCH_DIR]
RULE_PATH = _cfg["RULE_PATH"]
POLL_INTERVAL = _cfg["poll_interval"]
AUTO_FIX = _cfg["auto_fix"]
OLLAMA_URL = _cfg["ollama_url"]
OLLAMA_MODEL = _cfg["ollama_model"]
MAX_WORKERS = _cfg["max_workers"]
BACKUP_DIR = _cfg["BACKUP_DIR"]
