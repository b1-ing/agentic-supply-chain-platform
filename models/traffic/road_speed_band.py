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

    @property
    def link_id(self) -> str:

        #
        # Prefer an official identifier if LTA provides one
        #

        if "LinkID" in self.metadata:
            return str(self.metadata["LinkID"])

        #
        # Otherwise derive one from geometry
        #

        return (
            f"{self.start_lat:.6f}|"
            f"{self.start_lon:.6f}|"
            f"{self.end_lat:.6f}|"
            f"{self.end_lon:.6f}"
        )