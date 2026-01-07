import datetime
from typing import Dict

class TaskManager:
    """管理任务状态和节点执行结果"""
    def __init__(self):
        self.tasks: Dict[str, dict] = {}  # task_id -> {nodes, status, priority, queue_status, coro}

    def init_task(self, task_id: str, nodes: list, priority: int = 100):
        self.tasks[task_id] = {
            "nodes": {n.id: {"status": "pending", "result": None, "error": None,
                             "start": None, "end": None, "elapsed": 0, "param_history": [], "cached": False} for n in nodes},
            "status": "created",
            "priority": priority,
            "queue_status": "queued",
            "coro": None
        }

    def set_task_coro(self, task_id: str, coro_factory):
        if task_id in self.tasks:
            self.tasks[task_id]["coro"] = coro_factory

    def get_task_coro(self, task_id: str):
        return self.tasks.get(task_id, {}).get("coro")

    def set_task_queue_status(self, task_id: str, status: str, priority: int | None = None):
        if task_id not in self.tasks:
            return
        self.tasks[task_id]["queue_status"] = status
        if priority is not None:
            self.tasks[task_id]["priority"] = priority
        # 当进入运行态时，把总状态置为 running
        if status == "running":
            self.tasks[task_id]["status"] = "running"

    def update_node(self, task_id, node_id, status, result=None, error=None, start=None, end=None, elapsed=None):
        node = self.tasks[task_id]["nodes"][node_id]
        if status:
            node["status"] = status
        if result is not None:
            node["result"] = result
        if error is not None:
            node["error"] = error
        if start:
            node["start"] = start
        if end:
            node["end"] = end
        if elapsed is not None:
            node["elapsed"] = elapsed

        # 更新整体任务状态
        if all(n["status"] in ["success", "skipped"] for n in self.tasks[task_id]["nodes"].values()):
            self.tasks[task_id]["status"] = "done"
        elif any(n["status"] == "failed" for n in self.tasks[task_id]["nodes"].values()):
            self.tasks[task_id]["status"] = "failed"

    def get_task_state(self, task_id):
        return self.tasks.get(task_id)

    def list_tasks(self):
        data = []
        for tid, st in self.tasks.items():
            nodes = st.get("nodes", {})
            total = len(nodes)
            done = sum(1 for n in nodes.values() if n.get("status") in ("success", "skipped", "failed"))
            percent = int(done / total * 100) if total else 0
            data.append({
                "task_id": tid,
                "status": st.get("status"),
                "queue_status": st.get("queue_status"),
                "priority": st.get("priority", 100),
                "progress": percent,
                "total": total,
            })
        return sorted(data, key=lambda x: x.get("priority", 100))

task_manager = TaskManager()
