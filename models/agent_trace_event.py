from dataclasses import dataclass, field
from typing import Any, Literal
import time
import uuid


@dataclass
class AgentTraceEvent:
    type: Literal[
        "tool_start",
        "tool_end",
        "agent_final",
        "agent_error",
    ]
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool_name: str | None = None
    args: dict[str, Any] | None = None
    result: Any = None
    error: str | None = None
    duration_ms: float | None = None