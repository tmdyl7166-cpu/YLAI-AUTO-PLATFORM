# backend/core/task.py
from dataclasses import dataclass, field
from typing import Dict, List, Any
from dataclasses import dataclass, field
from typing import Dict, List, Any

@dataclass
class Node:
    id: str
    script: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    condition: Any | None = None


@dataclass
class Task:
    """顺序流水线任务定义"""
    script: str
    params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Node:
    """
    DAG 节点定义
    id: 唯一节点 id（字符串）
    script: 要执行的脚本名（必须已在 registry 注册）
    params: 参数字典（可包含占位符，运行时会注入 _upstream_results）
    depends_on: list[str] - 本节点依赖的节点 id 列表
    condition: 可选条件表达式（True/False/字符串表达式），False 或条件为假则跳过
    """
    id: str
    script: str
    params: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    condition: Any | None = None

    def to_dict(self):
        return {
            "id": self.id,
            "script": self.script,
            "params": self.params,
            "depends_on": self.depends_on,
            "condition": self.condition,
        }
