from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from models.traffic.traffic_incident import TrafficIncident


class MatchType(Enum):
    ROAD = "road"

    RADIUS = "radius"

    SLIP_ROAD = "slip_road"

    JUNCTION = "junction"

    MANUAL = "manual"

    SPEED_BAND = "speed_band"


@dataclass
class MatchedTrafficIncident:
    incident: TrafficIncident

    affected_edges: list[tuple[int, int, int]]

    match_type: MatchType

    confidence: float

    radius_m: float | None = None

    matched_road: str | None = None

    radius_m: float
