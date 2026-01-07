#!/usr/bin/env python3
"""
hx.py — 自动化检测与联动执行脚本（监听→规则引擎→执行器→WebSocket推送→AI审计优化→进度记录）

功能：
- 监听项目 ../YLAI-AUTO-PLATFORM/ 全局内容及 Task/ 目录
- TreatTask.md 按编号任务处理，不删除未完成任务
- 使用 Ollama 本地 AI (MODEL=gpt-oss:20b) 进行逻辑分析、优化、部署建议
- 已完成任务迁移到 CompletedTask.md
- 进度表只记录真实文件变化，防止重复记录
- 可选 watchdog/websockets 支持实时监听和推送
"""

import os
import time
import json
import threading
import queue
import hashlib
import logging
import argparse
from pathlib import Path
import requests
from Task.hxpz import build_prompt_for_task

# 可选依赖
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except Exception:
    Observer = None
    FileSystemEventHandler = object

try:
    import websockets
except Exception:
    websockets = None

# 环境变量
MODEL = os.getenv("MODEL", "gpt-oss:20b")
OLLAMA = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
API_TARGET = os.getenv("API_TARGET", "http://127.0.0.1:8001")

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT
TASK_DIR = PROJECT_ROOT / "Task"
TASK_DIR.mkdir(exist_ok=True)

# 文件
PENDING = TASK_DIR / "PendingTask.md"
TREAT = TASK_DIR / "TreatTask.md"
COMPLETED = TASK_DIR / "CompletedTask.md"
AI_TASK = TASK_DIR / "AITask.md"
PROGRESS = TASK_DIR / "进度表.md"

# 根目录 TreatTask 支持：优先使用根目录的 TreatTask.md
ROOT_TREAT = PROJECT_ROOT / "TreatTask.md"

# 哈希缓存，避免重复记录
file_hash_cache: dict[str, str] = {}

# 全局写入节流缓存
_last_task_write_ts: dict[str, float] = {}


# 识别.py 优点合并：TreatTask 解析与依赖排序（可选）

def parse_tasks(content: str) -> list[dict]:
    tasks: list[dict] = []
    current: dict | None = None
    for line in content.splitlines():
        s = line.strip()
        if s.startswith("*") and "*" in s[1:]:
            idx = s.find("*", 1)
            task_id = s[1:idx]
            desc = s[idx+1:].strip()
            current = {"id": task_id, "desc": desc, "deps": []}
            # 依赖提取：形如 "依赖: *1*, *2*"
            if "依赖" in desc:
                import re
                deps = re.findall(r"\*(\d+)\*", desc)
                current["deps"] = deps
            tasks.append(current)
        elif current:
            current["desc"] += "\n" + s
    return tasks


def sort_tasks(tasks: list[dict]) -> list[dict]:
    try:
        return sorted(tasks, key=lambda x: int(x.get("id", "0")))
    except Exception:
        return tasks

# 统一日志
logging.basicConfig(
    level=os.getenv("HX_LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s [%(threadName)s] %(name)s: %(message)s",
)
log = logging.getLogger("hx")

 

def collect_context() -> tuple[str, dict]:
    ctx = {
        "api_base": API_TARGET,
        "deps": {},
        "mounts": {},
        "ws": {},
        "structure": {},
        "policy": {
            "apis": {
                "health": 200,
                "scripts": 200,
                "status": 401,
                "modules": 401,
            }
        },
    }
    # health
    try:
        r = requests.get(f"{API_TARGET}/health", timeout=3)
        if r.status_code == 200:
            data = r.json().get("data") or {}
            ctx["deps"] = data.get("deps") or {}
            ctx["ws"] = data.get("ws") or {}
    except Exception:
        pass
    # basic structure
    for name in ("frontend", "backend", "ai-docker", "scripts"):
        p = ROOT / name
        if p.exists():
            try:
                files: list[str] = []
                for child in p.iterdir():
                    files.append(child.name)
                ctx["structure"][name] = files[:50]
            except Exception:
                ctx["structure"][name] = []
    context_str = (
        f"API={ctx['api_base']} deps={ctx['deps']} ws={ctx['ws']} "
        f"dirs={list(ctx['structure'])} policy={ctx['policy']}"
    )
    return context_str, ctx


def apply_changes(plan: dict, dry_run: bool = True) -> list[str]:
    notes: list[str] = []
    changes = plan.get("changes") or []
    for ch in changes:
        path = Path(ch.get("path", "")).resolve()
        op = ch.get("op", "write")
        content = ch.get("content", "")
        if not path:
            continue
        notes.append(f"plan change: {op} {path}")
        if dry_run:
            continue
        try:
            # backup
            if path.exists():
                backup = Path(str(path) + ".bak")
                backup.write_bytes(path.read_bytes())
            if op == "write":
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
            elif op == "append":
                path.parent.mkdir(parents=True, exist_ok=True)
                prev = (
                    path.read_text(encoding="utf-8") if path.exists() else ""
                )
                joiner = "\n" if prev and not prev.endswith("\n") else ""
                path.write_text(prev + joiner + content, encoding="utf-8")
            elif op == "patch":
                # naive replace marker
                prev = (
                    path.read_text(encoding="utf-8") if path.exists() else ""
                )
                path.write_text(content if content else prev, encoding="utf-8")
        except Exception as e:
            notes.append(f"apply failed: {path} {e}")
    return notes


def run_validation_suite() -> dict:
    # 支持模拟校验模式：仅解析结构一致性，避免重复的后端未健康日志
    if os.getenv("HX_SIM_VALIDATE", "0") == "1":
        try:
            # 结构一致性：检查主要页面、静态目录与监控脚本是否存在
            base = PROJECT_ROOT  # 仓库根（当前项目根）
            pages = [
                base / "frontend" / "pages" / p
                for p in [
                    "index.html",
                    "api-doc.html",
                    "run.html",
                    "monitor.html",
                    "visual_pipeline.html",
                ]
            ]
            static = base / "frontend" / "static"
            monitor_py = base / "backend" / "api" / "monitor.py"
            # 静态资源关键子目录
            static_dirs = [
                static / "js",
                static / "css",
            ]
            # WebSocket 端点模拟（仅构造 URL，不进行真实连接）
            ws_urls = [
                API_TARGET.replace("http", "ws") + "/ws/monitor",
                API_TARGET.replace("http", "ws") + "/ws/pipeline/demo",
            ]
            missing = [str(p) for p in pages if not p.exists()]
            ok = (
                all(p.exists() for p in pages)
                and static.exists()
                and all(d.exists() for d in static_dirs)
                and monitor_py.exists()
            )
            return {
                "ok": ok,
                "mode": "simulated",
                "missing": missing,
                "ws": ws_urls,
                "static": [str(d) for d in static_dirs],
            }
        except Exception as e:
            return {"ok": False, "mode": "simulated", "error": str(e)}
    # 真实校验：调用 full_suite
    try:
        import subprocess
        import json as _json
        proc = subprocess.run(
            ["python", "scripts/full_suite.py"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        out = proc.stdout.strip()
        data = _json.loads(out) if out.startswith("{") else {
            "raw": out,
            "ok": proc.returncode == 0,
        }
        return data
    except Exception as e:
        return {"ok": False, "error": str(e)}


def optimize_twice(task_id: str, content: str, dry_run: bool = True) -> dict:
    ctx_str, ctx = collect_context()
    prompt = build_prompt_for_task(task_id, content, ctx_str)
    raw = ollama_generate(prompt)
    # expect JSON; fallback to text
    try:
        plan = json.loads(raw)
    except Exception:
        plan = {"changes": [], "raw": raw}
    notes1 = apply_changes(plan, dry_run=dry_run)
    v1 = run_validation_suite()
    feedback = {
        "first_validation": v1,
        "notes": notes1,
    }
    # second round with feedback
    fb_str = json.dumps(v1, ensure_ascii=False)[:4000]
    prompt2 = prompt + "\n\n【校验反馈】\n" + fb_str + "\n请据此完善部署计划，确保联动一致性。"
    raw2 = ollama_generate(prompt2)
    try:
        plan2 = json.loads(raw2)
    except Exception:
        plan2 = {"changes": [], "raw": raw2}
    notes2 = apply_changes(plan2, dry_run=dry_run)
    v2 = run_validation_suite()
    return {
        "round1": feedback,
        "round2": {
            "notes": notes2,
            "second_validation": v2,
        },
    }


def read_text(p: Path) -> str:
    return p.read_text(encoding="utf-8") if p.exists() else ""


def write_text(p: Path, s: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    # 对 Task 目录写入进行限频，避免脚本/工具频繁触发刷新
    try:
        interval = float(os.getenv("HX_TASK_WRITE_INTERVAL_SEC", "10"))
    except Exception:
        interval = 10.0
    if TASK_DIR in p.parents or p == TASK_DIR:
        global _last_task_write_ts
        if '_last_task_write_ts' not in globals():
            _last_task_write_ts = {}
        now = time.time()
        last = _last_task_write_ts.get(str(p), 0.0)
        if now - last < interval:
            # 跳过高频写入，降低无意义刷新
            return
        _last_task_write_ts[str(p)] = now
    p.write_text(s, encoding="utf-8")


def append_text(p: Path, s: str):
    cur = read_text(p)
    write_text(p, (cur + ("\n" if cur and not cur.endswith("\n") else "") + s))


def dedupe_completed_task():
    try:
        text = read_text(COMPLETED)
        if not text:
            return
        import re
        # 宽松匹配：跨行 JSON 错误块（HTTPConnectionPool/Connection refused）
        err_pat = re.compile(
            (
                r"\{\s*\"error\"\s*:\s*\"HTTPConnectionPool"
                r".*?Connection refused.*?\"\s*\}\s*"
            ),
            re.DOTALL,
        )
        matches = list(err_pat.finditer(text))
        if len(matches) <= 1:
            return
        # 找到时间戳范围
        header_pat = re.compile(
            r"^## +(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?$",
            re.MULTILINE,
        )
        lines = text.splitlines()
        idx_map = [text[:m.start()].count("\n") for m in matches]
        ts_list = []
        for idx in idx_map:
            start = max(0, idx - 20)
            block = "\n".join(lines[start:idx])
            m = list(header_pat.finditer(block))
            ts_list.append(m[-1].group("ts") if m else None)
        first_ts = ts_list[0]
        last_ts = None
        for ts_val in ts_list[::-1]:
            if ts_val:
                last_ts = ts_val
                break
        # 保留首个错误块，移除其余，并在首个后追加摘要
        parts = []
        last_pos = 0
        for i, m in enumerate(matches):
            if i == 0:
                parts.append(text[last_pos:m.end()])
                last_pos = m.end()
            else:
                parts.append(text[last_pos:m.start()])
                last_pos = m.end()
        parts.append(text[last_pos:])
        new_text = "".join(parts)
        summary = (
            "\n### 错误摘要（AI 连接拒绝去重）\n"
            "- 类型：HTTPConnectionPool/Connection refused\n"
            f"- 时间范围：{first_ts or '未知'} 至 {last_ts or '未知'}\n"
            "- 去重：后续同类错误不再重复记录\n"
        )
        insert_after = matches[0].end()
        new_text = new_text[:insert_after] + summary + new_text[insert_after:]
        write_text(COMPLETED, new_text)
    except Exception:
        # 静默失败，避免影响主流程
        pass


def ts() -> str:
    return time.strftime("%F %T")


def file_hash(path: Path) -> str:
    if not path.exists():
        return ""
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()

# --- Ollama 集成 ---



def ensure_ollama_running() -> bool:
    try:
        r = requests.get(f"{OLLAMA}")
        return r.status_code < 500
    except Exception:
        return False


def ollama_generate(prompt: str) -> str:
    try:
        resp = requests.post(
            f"{OLLAMA}/api/generate",
            json={"model": MODEL, "prompt": prompt},
            timeout=120,
        )
        return resp.text
    except Exception as e:
        return json.dumps({"error": str(e)})

# --- WebSocket 推送 ---



async def ws_push(event: dict):
    if not websockets:
        return
    url = API_TARGET.replace("http", "ws") + "/ws/monitor"
    try:
        async with websockets.connect(url, ping_interval=None) as ws:
            await ws.send(json.dumps(event, ensure_ascii=False))
            try:
                await ws.recv()
            except Exception:
                pass
    except Exception:
        pass


def publish(event: dict):
    # 仅发布重要事件，减少无关日志噪音
    allow = os.getenv(
        "HX_EVENT_TYPES",
        "optimize_merge,progress,records:deduped",
    ).split(",")
    etype = str(event.get("type") or "")
    if etype not in allow:
        return
    if os.getenv("HX_PUBLISH", "1") != "1":
        return
    # 快照（可选）
    if os.getenv("HX_SNAPSHOT", "0") == "1":
        try:
            requests.post(
                f"{API_TARGET}/api/snapshot",
                json={"kind": "hx", "data": event},
                timeout=2,
            )
        except Exception:
            pass
    # WebSocket（仅发送允许类型）
    try:
        import asyncio
        asyncio.run(ws_push(event))
    except Exception:
        pass

# --- 规则引擎与执行器 ---

 
class RuleEngine:
    def decide(self, path: Path, kind: str, content: str) -> dict:
        # TreatTask.md 修改 -> 优化
        if path == TREAT and kind in ("modified", "created"):
            return {
                "action": "optimize",
                "reason": "TreatTask 更新，需逐条优化并迁移到 CompletedTask.md",
            }
        # CompletedTask 或其他文件 -> 进度记录
        if path != PROGRESS:
            return {"action": "progress", "reason": f"{path.name} 变化"}
        return {"action": None}


class Executor:
    def __init__(self):
        self.engine = RuleEngine()
        self.last_optimize_ts: float | None = None
        self.optimize_interval = float(os.getenv("HX_OPT_INTERVAL_SEC", "2.0"))
        self.completed_ids: set[str] = set()

    def optimize_and_merge(self):
        # 仅在 TreatTask 存在时进行
        treat_text = read_text(TREAT)
        if not treat_text.strip():
            return False, "TreatTask.md 空"

        now = time.time()
        if (
            self.last_optimize_ts is not None
            and now - self.last_optimize_ts < self.optimize_interval
        ):
            return False, f"优化跳过（限流 {self.optimize_interval}s）"
        self.last_optimize_ts = now

        parse_mode = os.getenv("HX_TREAT_PARSE_MODE", "simple")
        tasks_pairs: list[tuple[str, str]] = []
        if parse_mode == "deps":
            parsed = sort_tasks(parse_tasks(treat_text))
            for t in parsed:
                tasks_pairs.append((t["id"], t["desc"]))
        else:
            lines = treat_text.splitlines()
            buffer: list[str] = []
            task_id: str | None = None
            for line in lines:
                if line.strip().startswith("*") and "*" in line:
                    if task_id:
                        tasks_pairs.append((task_id, "\n".join(buffer)))
                    task_id = line.strip().split("*")[1]
                    buffer = [line]
                else:
                    buffer.append(line)
            if task_id:
                tasks_pairs.append((task_id, "\n".join(buffer)))

        remaining: list[str] = []
        for tid, content in tasks_pairs:
            if parse_mode == "deps":
                import re
                deps = re.findall(r"\*(\d+)\*", content)
                unmet = [d for d in deps if d not in self.completed_ids]
                if unmet:
                    remaining.append(content)
                    continue
            context = (
                "当前项目使用 FastAPI/Starlette/Uvicorn，"
                "静态资源通过 StrictStaticFiles 挂载；"
                "API 检查策略为 health/scripts=200，status/modules=401 可接受；"
                "前端页面包含 index/api-doc/monitor/run/visual_pipeline，"
                "WS 热重载已实现并去抖。"
            )
            prompt = build_prompt_for_task(str(tid), content, context)
            result = ollama_generate(prompt)
            append_text(COMPLETED, f"## {ts()} 任务 *{tid}*\n{result}\n")
            dedupe_completed_task()
            append_text(
                AI_TASK,
                f"- {ts()} 优化并迁移 TreatTask.md -> CompletedTask.md 任务编号: {tid}",
            )
            if "error" in result.lower() or not result.strip():
                remaining.append(content)
            else:
                self.completed_ids.add(str(tid))

        write_text(TREAT, "\n".join(remaining))
        done_cnt = len(tasks_pairs) - len(remaining)
        append_text(PROGRESS, f"- {ts()} 完成优化迁移任务 {done_cnt} 条")
        try:
            publish({
                "type": "HX_EVENT",
                "stage": "optimize_merge",
                "ok": True,
                "done": done_cnt,
            })
        except Exception:
            pass
        return True, f"优化迁移完成 {done_cnt} 条任务"

    def handle(self, path: Path, kind: str):
        content = read_text(path)
        decision = self.engine.decide(path, kind, content)
        act = decision.get("action")
        if act == "optimize":
            return self.optimize_and_merge()
        elif act == "progress":
            return self.record_progress(path, kind)
        return False, None

        if act == "optimize":
            return self.optimize_and_merge()
        elif act == "progress":
            return self.record_progress(path, kind)
        return False, None

# --- 文件监听 ---

 
class Handler(FileSystemEventHandler):
    def __init__(self, execu: Executor, q: queue.Queue):
        super().__init__()
        self.execu = execu
        self.q = q
    
    def on_modified(self, event):
        if getattr(event, "is_directory", False):
            return
        self.q.put((Path(event.src_path), "modified"))
        globals().setdefault("_last_change_ts", time.time())
        globals()["_last_change_ts"] = time.time()
    
    def on_created(self, event):
        if getattr(event, "is_directory", False):
            return
        self.q.put((Path(event.src_path), "created"))
        globals().setdefault("_last_change_ts", time.time())
        globals()["_last_change_ts"] = time.time()


def start_watch(
    paths,
    execu: Executor,
    stop_event: threading.Event,
    debounce_ms: int = 300,
    ignore_globs: list[str] | None = None,
):
    if not Observer:
        log.warning("watchdog 未安装，监听不可用")
        return None
    observer = Observer()
    q: queue.Queue = queue.Queue()
    handler = Handler(execu, q)
    for p in paths:
        observer.schedule(handler, str(p), recursive=True)
    observer.start()

    def loop():
        last_ts: dict[tuple[str, str], float] = {}
        pending: dict[tuple[str, str], tuple[Path, str]] = {}
        batch_counts: dict[tuple[str, str], int] = {}
        interval = max(50, debounce_ms) / 1000.0
        while not stop_event.is_set():
            try:
                path, kind = q.get(timeout=0.5)
            except queue.Empty:
                time.sleep(0.2)
                continue
            try:
                spath = str(path)
                # 忽略匹配的路径（如日志、缓存目录）
                if ignore_globs:
                    import fnmatch
                    if any(
                        fnmatch.fnmatch(spath, pat)
                        for pat in ignore_globs
                    ):
                        continue
                key = (spath, kind)
                now = time.time()
                last = last_ts.get(key, 0.0)
                if now - last < interval:
                    # 仅保留同键最后一次事件
                    pending[key] = (path, kind)
                    batch_counts[key] = batch_counts.get(key, 0) + 1
                    continue
                last_ts[key] = now
                if (
                    PROJECT_ROOT in path.parents
                    or TASK_DIR in path.parents
                    or path in (TREAT, COMPLETED)
                ):
                    ok, msg = execu.handle(path, kind)
                    if ok and msg:
                        log.info(msg)
            except Exception as e:
                log.exception("监听处理异常: %s", e)
            # 将挂起的事件合并处理
            try:
                for k, (p2, k2) in list(pending.items()):
                    last_ts[k] = time.time()
                    ok, msg = execu.handle(p2, k2)
                    if ok:
                        count = batch_counts.get(k, 0)
                        if msg:
                            # 在日志中包含批次大小
                            log.info("%s (debounce batch=%d)", msg, count)
                    # 清理该键计数
                    batch_counts.pop(k, None)
                    pending.pop(k, None)
            except Exception as e:
                log.exception("debounce 处理异常: %s", e)
        # 退出时尝试清理 observer
    threading.Thread(target=loop, daemon=True).start()
    return observer

# --- 处理旧 PendingTask.md ---

 
def legacy_run_once(dry_run: bool = False):
    pending = read_text(PENDING).strip()
    if not pending:
        return False
    prompt = (
        "Complete the following task with concise, actionable steps and "
        "results.\n\n"
        f"{pending}\n"
    )
    if dry_run:
        log.info("[dry-run] 将处理 PendingTask.md -> CompletedTask.md")
        return True
    else:
        output = ollama_generate(prompt)
        write_text(COMPLETED, f"## {ts()}\n\n{output}\n")
        dedupe_completed_task()
        append_text(AI_TASK, f"- {ts()} {MODEL} processed PendingTask.md")
        append_text(
            PROGRESS,
            f"- {ts()} 处理 PendingTask.md -> CompletedTask.md",
        )
        write_text(PENDING, "")
    return True


def main():
    parser = argparse.ArgumentParser(description="HX watcher & executor")
    parser.add_argument(
        "--debounce",
        type=int,
        default=int(os.getenv("HX_DEBOUNCE_MS", "300")),
        help="debounce ms",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="do not write files, only log",
    )
    parser.add_argument(
        "--ignore",
        action="append",
        default=[],
        help="glob patterns to ignore (can repeat)",
    )
    args = parser.parse_args()
    log.info("MODEL=%s OLLAMA=%s API=%s", MODEL, OLLAMA, API_TARGET)
    watch_paths = [PROJECT_ROOT, TASK_DIR]
    execu = Executor()
    stop_event = threading.Event()
    obs = start_watch(
        watch_paths,
        execu=execu,
        stop_event=stop_event,
        debounce_ms=args.debounce,
        ignore_globs=(
            args.ignore or ["**/__pycache__/**", "logs/**", "**/*.tmp"]
        ),
    )
    legacy_run_once(dry_run=args.dry_run)
    # 可通过环境变量禁用目录监听，仅在启动时进行一次识别与写入
    watch_disable = os.getenv("HX_WATCH_DISABLE", "0") == "1"
    try:
        if watch_disable:
            # 一次性处理并退出
            try:
                treat_path = ROOT_TREAT if ROOT_TREAT.exists() else TREAT
                if treat_path.exists() and read_text(treat_path).strip():
                    res = optimize_twice(
                        "Treat",
                        read_text(treat_path),
                        dry_run=args.dry_run,
                    )
                    log.info(
                        "闭环结果: %s",
                        json.dumps(res, ensure_ascii=False)[:1000],
                    )
                    ok, msg = execu.optimize_and_merge()
                    if ok and msg:
                        log.info(msg)
            except Exception as e:
                log.exception("Treat 一次性处理异常: %s", e)
            return
        globals().setdefault("_last_change_ts", time.time())
        sleep_after = float(os.getenv("HX_IDLE_SLEEP_SEC", "20"))
        while True:
            try:
                # 沉睡策略：若超过阈值未检测到任何修改，则跳过 AI 闭环，仅监听
                now = time.time()
                last_change = globals().get("_last_change_ts", now)
                if now - last_change > sleep_after:
                    time.sleep(1)
                    continue
                treat_path = ROOT_TREAT if ROOT_TREAT.exists() else TREAT
                if treat_path.exists() and read_text(treat_path).strip():
                    # 先运行两轮闭环（dry-run 受 --dry-run 控制）
                    res = optimize_twice(
                        "Treat",
                        read_text(treat_path),
                        dry_run=args.dry_run,
                    )
                    log.info(
                        "闭环结果: %s",
                        json.dumps(res, ensure_ascii=False)[:1000],
                    )
                    # 然后执行原有合并流程（真实迁移，受频率限制）
                    ok, msg = execu.optimize_and_merge()
                    if ok and msg:
                        log.info(msg)
            except Exception as e:
                log.exception("Treat 轮询异常: %s", e)
            time.sleep(3)
    except KeyboardInterrupt:
        if obs:
            stop_event.set()
            try:
                obs.stop()
                obs.join()
            except Exception as e:
                log.exception("observer 停止异常: %s", e)

if __name__ == "__main__":
    main()
