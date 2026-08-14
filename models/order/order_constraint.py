from __future__ import annotations

from pydantic import BaseModel
from enum import Enum
from typing import Any


class ConstraintType(str, Enum):
    AVOID_ROAD = "avoid_road"
    AVOID_AREA = "avoid_area"
    REQUIRED_ROAD = "required_road"
    REQUIRED_AREA = "required_area"
    REQUIRED_WAYPOINT = "required_waypoint"
    MAX_ROUTE_TIME = "max_route_time"
    MAX_ROUTE_DISTANCE = "max_route_distance"
    MINIMIZE_UNNECESSARY_DELAY = "minimize_unnecessary_delay"


class OrderConstraint(BaseModel):
    type: ConstraintType
    value: Any
    hard: bool = True
    reason: str | None = None