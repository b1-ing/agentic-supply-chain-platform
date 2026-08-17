from dataclasses import dataclass, field
from typing import Any, Literal
import time
import uuid


@dataclass
class AgentTraceEvent:
        """
        Represents a single observable event in an Operations Agent execution trace.

        Trace events record the lifecycle of tool calls and the final outcome of
        an agent run. They provide a structured record of what the agent attempted,
        what tools were invoked, what they returned, and whether execution failed.

        Event types:
            tool_start:
                Emitted when the agent begins executing a tool. Typically contains
                the tool name and arguments.

            tool_end:
                Emitted when a tool finishes successfully. Contains the tool name,
                arguments, result, and execution duration where available.

            agent_final:
                Emitted when the agent produces its final response to the user.

            agent_error:
                Emitted when the agent execution fails. The error field contains
                the associated error message.

        Attributes:
            type: The kind of event represented by this trace entry.
            id: Unique identifier for the trace event.
            tool_name: Name of the tool associated with the event, if applicable.
            args: Arguments supplied to the tool, if applicable.
            result: Result returned by the tool or associated event.
            error: Error message when the event represents a failed operation.
            duration_ms: Execution duration in milliseconds, when available.

        Trace events are intended for observability and debugging rather than
        operational state. They should not be treated as a source of truth for
        orders, vehicles, routes, or other WorldState data.
        """
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