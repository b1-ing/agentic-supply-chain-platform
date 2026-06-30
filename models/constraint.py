# models/constraints.py

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any


class ConstraintAction(Enum):
    REMOVE = "remove"
    PENALIZE = "penalize"
    LIMIT = "limit"


@dataclass
class RoutingConstraint:
    id: str

    action: ConstraintAction

    affected_edges: list[int]

    value: float | None

    start: datetime | None

    end: datetime | None

    confidence: float

    reason: str

    metadata: dict[str, Any]
