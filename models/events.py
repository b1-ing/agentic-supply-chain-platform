from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(kw_only=True)
class Event:
    timestamp: datetime
    source: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass(kw_only=True)
class TrafficIncident(Event):
    incident_type: str
    latitude: float
    longitude: float
    message: str


@dataclass(kw_only=True)
class RoadSpeedObservation(Event):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float
    speed_band: int
