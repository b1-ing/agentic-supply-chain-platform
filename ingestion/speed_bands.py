from datetime import datetime

from services.lta_service import LTADataMallClient
from models.traffic.road_speed_band import RoadSpeedBand


class SpeedBandService:

    def __init__(self, client: LTADataMallClient):
        self.client = client

    def fetch(self) -> list[RoadSpeedBand]:

        raw = self.client.fetch_all_pages("v4/TrafficSpeedBands")

        observations = []

        for item in raw:

            observations.append(
                RoadSpeedBand(
                    start_lat=float(item["StartLat"]),
                    start_lon=float(item["StartLon"]),
                    end_lat=float(item["EndLat"]),
                    end_lon=float(item["EndLon"]),
                    speed_band=int(item["SpeedBand"]),
                    timestamp=datetime.utcnow(),
                    metadata=item,
                )
            )

        return observations