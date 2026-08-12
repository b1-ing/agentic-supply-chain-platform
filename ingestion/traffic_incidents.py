from datetime import datetime

from services.lta_service import LTADataMallClient
from models.events import TrafficIncident


class TrafficIncidentService:
    def __init__(self, client: LTADataMallClient):
        self.client = client

    def fetch(self) -> list[TrafficIncident]:

        raw_incidents = self.client.fetch_all_pages("TrafficIncidents")

        incidents = []

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
