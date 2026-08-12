from enum import Enum

from pydantic.dataclasses import dataclass


@dataclass
class IncidentType(str, Enum):
    ACCIDENT = "accident"
    ROADWORKS = "roadworks"
    HEAVY_TRAFFIC = "heavy_traffic"
    ROAD_CLOSURE = "road_closure"
    VEHICLE_BREAKDOWN = "vehicle_breakdown"
    FLOOD = "flood"
    EVENT = "event"
    HAZARD = "hazard"
    OTHER = "other"
