from datetime import datetime
from typing import List

from services.lta_service import LTADataMallClient
from models.events import (
    TrafficIncident,
    RoadSpeedObservation,
)


class TrafficService:
    """
    Service responsible for retrieving traffic-related data from the
    LTA DataMall API and converting it into the application's
    internal event models.
    """

    def __init__(self, client: LTADataMallClient):
        self.client = client

    def fetch_live_incidents(self) -> List[TrafficIncident]:
        """
        Fetches live traffic incidents.

        Returns
        -------
        List[TrafficIncident]
        """

        raw_incidents = self.client.fetch_all_pages("TrafficIncidents")

        incidents: List[TrafficIncident] = []

        for item in raw_incidents:
            latitude = item.get("Latitude")
            longitude = item.get("Longitude")

            if latitude is None or longitude is None:
                continue

            incidents.append(
                TrafficIncident(
                    incident_type=item.get("Type", "Unknown"),
                    latitude=float(latitude),
                    longitude=float(longitude),
                    message=item.get("Message", ""),
                    timestamp=datetime.utcnow(),
                    source="LTA",
                    raw=item,
                )
            )

        return incidents

    def fetch_speed_bands(self) -> List[RoadSpeedObservation]:
        """
        Fetches current traffic speed bands.

        Returns
        -------
        List[RoadSpeedObservation]
        """

        raw_speed_data = self.client.fetch_all_pages("TrafficSpeedBands")

        observations: List[RoadSpeedObservation] = []

        for item in raw_speed_data:
            observations.append(
                RoadSpeedObservation(
                    start_lat=float(item["StartLat"]),
                    start_lon=float(item["StartLon"]),
                    end_lat=float(item["EndLat"]),
                    end_lon=float(item["EndLon"]),
                    speed_band=int(item["SpeedBand"]),
                    timestamp=datetime.utcnow(),
                    source="LTA",
                    raw=item,
                )
            )

        return observations
