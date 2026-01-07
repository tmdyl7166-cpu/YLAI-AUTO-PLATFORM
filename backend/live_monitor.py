import time
import asyncio
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import json
import os
import sys
from datetime import datetime

# 获取项目根目录
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

# 添加backend路径
sys.path.append(str(ROOT / 'backend'))

LOG_FILE = "logs/ai_router.log"
METRICS_FILE = "logs/ai_metrics.json"

try:
    from backend.scripts.ai_coordinator import AIModelCoordinator
    ai_coordinator = None
except ImportError:
    ai_coordinator = None

class Watcher(FileSystemEventHandler):
    def on_modified(self, event):
        print(f"[文件修改] {event.src_path}")

def start_file_watch(path="."):
    observer = Observer()
    observer.schedule(Watcher(), path=path, recursive=True)
    observer.start()
    return observer

def tail_log(file_path: str):
    # 简易 tail -f
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    print(f"[日志] {line.strip()}")
                else:
                    time.sleep(0.5)
    except FileNotFoundError:
        print(f"[日志] 文件不存在：{file_path}，等待创建...")
        time.sleep(1)
        return tail_log(file_path)

async def monitor_ai_models():
    """监控AI模型状态"""
    while True:
        try:
            if ai_coordinator:
                # 获取模型状态
                status = await ai_coordinator.run('get_model_status')
                metrics = await ai_coordinator.run('get_performance_metrics')

                # 保存监控数据
                monitor_data = {
                    'timestamp': datetime.now().isoformat(),
                    'models': status.get('models', {}),
                    'metrics': metrics.get('metrics', {}),
                    'coordinator_status': 'active'
                }

                # 确保日志目录存在
                os.makedirs('logs', exist_ok=True)

                # 保存到文件
                with open(METRICS_FILE, 'w', encoding='utf-8') as f:
                    json.dump(monitor_data, f, ensure_ascii=False, indent=2)

                print(f"[AI监控] {datetime.now().strftime('%H:%M:%S')} - 模型状态已更新")
            else:
                print("[AI监控] 协调器未初始化")

        except Exception as e:
            print(f"[AI监控] 错误: {e}")

        await asyncio.sleep(30)  # 每30秒监控一次

def start_ai_monitor():
    """启动AI监控线程"""
    def run_monitor():
        asyncio.run(monitor_ai_models())

    monitor_thread = threading.Thread(target=run_monitor, daemon=True)
    monitor_thread.start()
    return monitor_thread

def start_monitor():
    # 初始化AI协调器
    global ai_coordinator
    if ai_coordinator is None:
        try:
            ai_coordinator = AIModelCoordinator()
            asyncio.run(ai_coordinator.initialize())
            print("✅ AI协调器监控初始化成功")
        except Exception as e:
            print(f"❌ AI协调器监控初始化失败: {e}")

    # 启动AI监控
    ai_monitor_thread = start_ai_monitor()

    # 启动文件监控
    observer = start_file_watch(".")

    try:
        tail_log(LOG_FILE)
    except KeyboardInterrupt:
        observer.stop()
        ai_monitor_thread.join()
    observer.join()

if __name__ == "__main__":
    start_monitor()
