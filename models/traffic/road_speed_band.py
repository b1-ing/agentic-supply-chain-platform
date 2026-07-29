from dataclasses import dataclass
from datetime import datetime


@dataclass
class RoadSpeedBand:
    start_lat: float
    start_lon: float

    end_lat: float
    end_lon: float

    speed_band: int

    timestamp: datetime

    metadata: dict