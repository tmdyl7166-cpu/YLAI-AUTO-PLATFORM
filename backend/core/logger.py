import logging
import os
from pathlib import Path

_default_logs = Path(__file__).resolve().parent.parent / "logs"
LOG_DIR = Path(os.getenv("LOG_DIR", str(_default_logs))).resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)


def _mk_file_handler(filename: str, level: int):
    fh = logging.FileHandler(str(LOG_DIR / filename), encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    return fh


root = logging.getLogger()
root.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO")))

# 控制台简洁输出
ch = logging.StreamHandler()
ch.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
ch.setFormatter(logging.Formatter(
    fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
))

# 文件分层日志
system_handler = _mk_file_handler("system.log", logging.INFO)
api_handler = _mk_file_handler("api.log", logging.INFO)
task_handler = _mk_file_handler("task.log", logging.INFO)
ws_handler = _mk_file_handler("ws.log", logging.INFO)

# 各类 logger
system_logger = logging.getLogger("system")
api_logger = logging.getLogger("api")
task_logger = logging.getLogger("task")
ws_logger = logging.getLogger("ws")

for lg, h in [
    (system_logger, system_handler),
    (api_logger, api_handler),
    (task_logger, task_handler),
    (ws_logger, ws_handler),
]:
    lg.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO")))
    # 每类既写文件也到控制台，便于 VS Code单独追踪
    lg.addHandler(h)
    lg.addHandler(ch)

# 兼容旧引用
logger = system_logger

# === 简易 WS 广播订阅（供 /ws/logs 使用） ===
_ws_subscribers = []

def make_event(level: str, name: str, message: str, **kwargs) -> str:
    """统一WS事件格式，前端可直接解析。
    字段：level,name,message,layer(optional),elapsed_ms(optional),status(optional),error(optional)
    输出为紧凑JSON字符串。
    """
    import json
    evt = {
        "level": level,
        "name": name,
        "message": message,
    }
    evt.update({k: v for k, v in kwargs.items() if v is not None})
    return json.dumps(evt, ensure_ascii=False)


def register_ws_sender(sender):
    """注册一个异步发送函数：async def sender(text:str) -> None"""
    _ws_subscribers.append(sender)


async def emit_ws(text: str):
    for send in list(_ws_subscribers):
        try:
            await send(text)
        except Exception:
            # 失败的订阅者忽略；由 WS 端自行移除
            pass

async def emit_event(level: str, name: str, message: str, **kwargs):
    """封装事件生成与发送。"""
    await emit_ws(make_event(level, name, message, **kwargs))
