from typing import Dict, List
from fastapi import WebSocket
from backend.ws.task_manager import task_manager
import asyncio

class WSManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        if task_id not in self.connections:
            self.connections[task_id] = []
        self.connections[task_id].append(websocket)

    def disconnect(self, task_id: str, websocket: WebSocket):
        if task_id in self.connections:
            self.connections[task_id].remove(websocket)
            if not self.connections[task_id]:
                del self.connections[task_id]

    async def broadcast(self, task_id: str, message: dict):
        if task_id not in self.connections:
            return
        dead = []
        for ws in self.connections[task_id]:
            try:
                await ws.send_json(message)
            except:
                dead.append(ws)
        for ws in dead:
            self.disconnect(task_id, ws)

    async def broadcast_node_update(self, task_id: str, node_id: str):
        state = task_manager.get_task_state(task_id)
        if not state:
            return
        node_state = state["nodes"][node_id]
        await self.broadcast(task_id, {
            "type": "node_update",
            "node_id": node_id,
            "status": node_state["status"],
            "result": node_state["result"],
            "error": node_state["error"],
            "elapsed": node_state["elapsed"],
            "cached": node_state.get("cached", False)
        })

ws_manager = WSManager()
