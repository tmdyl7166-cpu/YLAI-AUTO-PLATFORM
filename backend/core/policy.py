from pathlib import Path
import yaml


POLICY_PATH = Path(__file__).resolve().parent.parent / "config" / "global_policy.yaml"


class GlobalPolicy:
    _cache = None

    @classmethod
    def load(cls) -> dict:
        if cls._cache is None:
            with open(POLICY_PATH, "r", encoding="utf-8") as f:
                cls._cache = yaml.safe_load(f) or {}
        return cls._cache

    @classmethod
    def level(cls) -> int:
        return int(cls.load().get("policy_level", 0))

    @classmethod
    def allow_ai_fix(cls) -> bool:
        return bool(cls.load().get("ai", {}).get("auto_param_fix", False))

    @classmethod
    def max_concurrency(cls) -> int:
        return int(cls.load().get("network", {}).get("max_concurrency", 4))

    @classmethod
    def request_interval_ms(cls) -> int:
        return int(cls.load().get("network", {}).get("request_interval_ms", 1000))

    @classmethod
    def obey_robots(cls) -> bool:
        return bool(cls.load().get("crawler", {}).get("obey_robots", True))

    @classmethod
    def rate_limit_guard(cls) -> bool:
        return bool(cls.load().get("safety", {}).get("enable_rate_limit_guard", True))

    @classmethod
    def kill_switch(cls) -> bool:
        return bool(cls.load().get("safety", {}).get("enable_task_kill_switch", True))
