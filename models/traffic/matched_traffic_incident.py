from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

@dataclass
class MatchedTrafficIncident:
    incident: TrafficIncident

    affected_edges: list[tuple[int, int, int]]

    match_type: MatchType

    confidence: float

    radius_m: float


class MatchType(Enum):
    ROAD = "road"

    RADIUS = "radius"

    SLIP_ROAD = "slip_road"

    JUNCTION = "junction"

    MANUAL = "manual"
