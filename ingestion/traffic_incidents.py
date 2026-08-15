from datetime import datetime, timezone
from uuid import uuid4

from services.lta_service import LTADataMallClient
from models.traffic.traffic_incident import TrafficIncident
from models.traffic.incident_type import IncidentType


class TrafficIncidentService:
    """
    Ingests LTA traffic incidents and converts them into the
    platform's canonical TrafficIncident model.
    """

    def __init__(self, client: LTADataMallClient):
        self.client = client

    def fetch(self) -> list[TrafficIncident]:
        """
        Fetch the latest LTA traffic incidents and normalize them
        into TrafficIncident objects used by WorldState.
        """

        raw_incidents = self.client.fetch_all_pages(
            "TrafficIncidents"
        )

        incidents: list[TrafficIncident] = []

        for item in raw_incidents:
            incident = self._parse_incident(item)

            if incident is not None:
                incidents.append(incident)

        return incidents

    def _parse_incident(
        self,
        item: dict,
    ) -> TrafficIncident | None:
        """
        Convert one raw LTA incident into a TrafficIncident.

        Incidents without coordinates are ignored because they
        cannot currently be spatially matched to the road graph.
        """

        latitude = item.get("Latitude")
        longitude = item.get("Longitude")

        if latitude is None or longitude is None:
            return None

        incident_type = self._parse_incident_type(
            item.get("Type")
        )

        description = item.get("Message", "")

        now = datetime.now(timezone.utc)

        return TrafficIncident(
            incident_id=str(uuid4()),
            source="LTA",
            type=incident_type,
            severity=self._derive_severity(incident_type),
            description=description,
            road_name=self._extract_road_name(description),
            latitude=float(latitude),
            longitude=float(longitude),
            start_time=now,
            end_time=None,
            metadata={
                "raw": item,
            },
        )

    @staticmethod
    def _parse_incident_type(
        value: str | None,
    ) -> IncidentType:
        """
        Convert the LTA incident type into the platform's
        IncidentType enum.
        """

        if not value:
            return IncidentType.OTHER

        normalized = value.strip().lower()

        mapping = {
            "accident": IncidentType.ACCIDENT,
            "vehicle breakdown": IncidentType.VEHICLE_BREAKDOWN,
            "roadwork": IncidentType.ROADWORKS,
            "road works": IncidentType.ROADWORKS,
            "heavy traffic": IncidentType.HEAVY_TRAFFIC,
            "road closure": IncidentType.ROAD_CLOSURE,
            "flood": IncidentType.FLOOD,
            "event": IncidentType.EVENT,
            "hazard": IncidentType.HAZARD,
        }

        return mapping.get(
            normalized,
            IncidentType.OTHER,
        )

    @staticmethod
    def _derive_severity(
        incident_type: IncidentType,
    ) -> float:
        """
        Assign a basic operational severity based on incident type.
        """

        severity = {
            IncidentType.ACCIDENT: 1.0,
            IncidentType.ROADWORKS: 0.4,
            IncidentType.HEAVY_TRAFFIC: 0.7,
            IncidentType.ROAD_CLOSURE: 1.0,
            IncidentType.VEHICLE_BREAKDOWN: 0.6,
            IncidentType.FLOOD: 1.0,
            IncidentType.EVENT: 0.3,
            IncidentType.HAZARD: 0.8,
            IncidentType.OTHER: 0.5,
        }

        return severity[incident_type]

    @staticmethod
    def _extract_road_name(
        description: str,
    ) -> str | None:
        """
        Extract a known Singapore expressway from the LTA message.

        General road matching should ultimately be handled by
        RoadMatcher.
        """

        roads = (
            "PIE",
            "AYE",
            "KJE",
            "BKE",
            "CTE",
            "ECP",
            "KPE",
            "MCE",
            "SLE",
            "TPE",
        )

        upper_description = description.upper()

        for road in roads:
            if road in upper_description:
                return road

        return None