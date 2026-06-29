# models/constraint.py
from pydantic import BaseModel
from typing import List, Tuple, Optional

class TrafficIncidentConstraint(BaseModel):
    incident_id: Optional[str] = None
    type: str          # e.g., "Accident", "Roadwork"
    latitude: float
    longitude: float
    message: str       # e.g., "Accident on AYE (towards Tuas) after Exit 27."

class RoadSpeedConstraint(BaseModel):
    start_coord: Tuple[float, float] # (lat, lon)
    end_coord: Tuple[float, float]   # (lat, lon)
    speed_band: int                  # 1-8 scale from LTA