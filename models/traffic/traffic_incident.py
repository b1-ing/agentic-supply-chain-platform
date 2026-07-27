from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


@dataclass
class TrafficIncident:
    incident_id: str

    source: str

    type: IncidentType

    severity: float

    description: str

    road_name: str | None

    latitude: float | None

    longitude: float | None

    start_time: datetime

    end_time: datetime | None

    metadata: dict = field(default_factory=dict)


