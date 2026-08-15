from models.traffic.traffic_incident import TrafficIncident


def serialize_traffic_incident(
    incident: TrafficIncident,
) -> dict:
    return {
        "incident_id": incident.incident_id,
        "source": incident.source,
        "type": incident.type.value,
        "severity": incident.severity,
        "description": incident.description,
        "road_name": incident.road_name,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "start_time": incident.start_time.isoformat(),
        "end_time": (
            incident.end_time.isoformat()
            if incident.end_time is not None
            else None
        ),
        "metadata": incident.metadata,
    }