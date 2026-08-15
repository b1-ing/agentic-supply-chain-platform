from datetime import datetime

from pydantic import BaseModel


class TrafficIncidentResponse(BaseModel):
    incident_id: str
    source: str
    type: str
    severity: float
    description: str
    road_name: str | None
    latitude: float | None
    longitude: float | None
    start_time: datetime
    end_time: datetime | None
    metadata: dict