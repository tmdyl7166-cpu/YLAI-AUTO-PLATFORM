from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional

@dataclass
class FuzzParam:
    name: str
    value: Any
    kind: str  # e.g., 'string', 'number', 'json', 'file'

@dataclass
class FuzzCase:
    endpoint: str
    method: str = 'GET'
    params: List[FuzzParam] = field(default_factory=list)
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None

@dataclass
class FuzzResult:
    ok: bool
    status: int
    elapsed_ms: float
    length: int
    content_type: str
    keywords: List[str] = field(default_factory=list)
    error: Optional[str] = None
    request_snapshot: Dict[str, Any] = field(default_factory=dict)
    response_snapshot: Dict[str, Any] = field(default_factory=dict)
