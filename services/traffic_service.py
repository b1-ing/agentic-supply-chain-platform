# services/traffic_service.py
from services.lta_base_client import LTADataMallClient
from models.constraint import TrafficIncidentConstraint, RoadSpeedConstraint
from typing import List

class TrafficService:
    def __init__(self, client: LTADataMallClient):
        self.client = client

    def fetch_live_incidents(self) -> List[TrafficIncidentConstraint]:
        """
        Fetches current incidents and parses them into your standardized internal models
        """
        # Endpoint 22 from the User Guide
        raw_data = self.client.fetch_all_pages("TrafficIncidents")

        normalized_incidents = []
        for item in raw_data:
            # Skip items that don't provide coordinates
            if not item.get("Latitude") or not item.get("Longitude"):
                continue

            normalized_incidents.append(
                TrafficIncidentConstraint(
                    type=item.get("Type", "Unknown"),
                    latitude=float(item.get("Latitude")),
                    longitude=float(item.get("Longitude")),
                    message=item.get("Message", "")
                )
            )
        return normalized_incidents

    def fetch_speed_bands(self) -> List[RoadSpeedConstraint]:
        """
        Fetches live speed segments across the network
        """
        # Endpoint 23 from the User Guide
        raw_data = self.client.fetch_all_pages("TrafficSpeedBands")

        normalized_speeds = []
        for item in raw_data:
            normalized_speeds.append(
                RoadSpeedConstraint(
                    start_coord=(float(item["StartLat"]), float(item["StartLon"])),
                    end_coord=(float(item["EndLat"]), float(item["EndLon"])),
                    speed_band=int(item["SpeedBand"])
                )
            )
        return normalized_speeds