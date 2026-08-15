# agents/tools/traffic_tools.py

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from models.traffic.traffic_incident import TrafficIncident
from models.traffic.incident_type import IncidentType
from services.world.world_manager import world_manager


# ============================================================
# REPORT TRAFFIC INCIDENT
# ============================================================

async def report_traffic_incident(
    road_name: str | None = None,
    incident_type: str = "ROAD_CLOSURE",
    description: str = "",
    severity: float = 1.0,
    latitude: float | None = None,
    longitude: float | None = None,
    end_time: datetime | None = None,
) -> dict:
    """
    Report a new traffic incident to the WorldState.

    Use this when the user reports a new disruption such as:

        "PIE is closed"
        "There is an accident on Braddell Road"
        "Roadworks on CTE"

    The incident is persisted in world.traffic_events.

    This tool does NOT reroute vehicles.
    """

    world = world_manager.get_world()

    # --------------------------------------------------------
    # Validate incident type
    # --------------------------------------------------------

    try:
        incident_type_enum = IncidentType(incident_type)
    except ValueError:
        valid_types = [
            incident.value
            for incident in IncidentType
        ]

        return {
            "success": False,
            "error": (
                f"Unknown incident type '{incident_type}'. "
                f"Valid types: {valid_types}"
            ),
        }

    # --------------------------------------------------------
    # Validate road/area information
    # --------------------------------------------------------

    if not road_name and latitude is None and longitude is None:
        return {
            "success": False,
            "error": (
                "A traffic incident requires either "
                "road_name or geographic coordinates."
            ),
        }

    # --------------------------------------------------------
    # Create incident
    # --------------------------------------------------------

    incident = TrafficIncident(
        incident_id=f"INC-{uuid4().hex[:8].upper()}",
        source="AGENT",
        type=incident_type_enum,
        severity=severity,
        description=description,
        road_name=road_name,
        latitude=latitude,
        longitude=longitude,
        start_time=datetime.now(),
        end_time=end_time,
    )

    # --------------------------------------------------------
    # Persist
    # --------------------------------------------------------

    world.traffic_events.append(incident)

    return {
        "success": True,
        "incident_id": incident.incident_id,
        "type": incident.type.value,
        "road_name": incident.road_name,
        "severity": incident.severity,
        "description": incident.description,
        "message": (
            f"Traffic incident {incident.incident_id} "
            f"reported successfully."
        ),
    }


# ============================================================
# GET ACTIVE TRAFFIC INCIDENTS
# ============================================================

async def get_traffic_incidents() -> dict:
    """
    Return currently active traffic incidents.

    This is primarily an observation tool for the agent.
    """

    world = world_manager.get_world()

    now = datetime.now(timezone.utc)

    incidents = []

    for incident in world.traffic_events:

        if now < incident.start_time:
            continue

        if (
            incident.end_time is not None
            and now > incident.end_time
        ):
            continue

        incidents.append(
            {
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
            }
        )

    return {
        "success": True,
        "incident_count": len(incidents),
        "incidents": incidents,
    }
# ============================================================
# FIND AFFECTED ROUTES
# ============================================================

async def find_affected_routes(
    incident_id: str,
) -> dict:
    """
    Determine which active vehicle routes are affected by
    a traffic incident.

    This should use deterministic routing/network logic rather
    than asking the LLM to decide which routes are affected.
    """

    world = world_manager.get_world()

    # --------------------------------------------------------
    # Find incident
    # --------------------------------------------------------

    incident = next(
        (
            incident
            for incident in world.traffic_events
            if incident.incident_id == incident_id
        ),
        None,
    )

    if incident is None:
        return {
            "success": False,
            "error": (
                f"Traffic incident '{incident_id}' not found."
            ),
        }

    # --------------------------------------------------------
    # Import here to avoid circular dependencies
    # --------------------------------------------------------

    from services.traffic.disruption_service import (
        DisruptionService,
    )

    service = DisruptionService()

    affected = service.find_affected_routes(
        world=world,
        incident=incident,
    )

    return {
        "success": True,
        "incident_id": incident_id,
        "affected_route_count": len(affected),
        "affected_routes": [
            {
                "route_id": route.route_id,
                "vehicle_id": route.vehicle_id,
            }
            for route in affected
        ],
    }


# ============================================================
# REROUTE AFFECTED ROUTES
# ============================================================

async def reroute_affected_routes(
    incident_id: str,
) -> dict:
    """
    Reroute all currently active vehicle routes affected by
    a traffic incident.

    The disruption service determines the affected routes and
    reconstructs the remaining route from the vehicle's current
    position.

    Completed stops are not re-routed.
    """

    world = world_manager.get_world()

    # --------------------------------------------------------
    # Find incident
    # --------------------------------------------------------

    incident = next(
        (
            incident
            for incident in world.traffic_events
            if incident.incident_id == incident_id
        ),
        None,
    )

    if incident is None:
        return {
            "success": False,
            "error": (
                f"Traffic incident '{incident_id}' not found."
            ),
        }

    # --------------------------------------------------------
    # Ensure incident is active
    # --------------------------------------------------------

    now = datetime.now()

    if now < incident.start_time:
        return {
            "success": False,
            "error": "Traffic incident has not started yet.",
        }

    if (
        incident.end_time is not None
        and now > incident.end_time
    ):
        return {
            "success": False,
            "error": "Traffic incident is no longer active.",
        }

    # --------------------------------------------------------
    # Reroute through service
    # --------------------------------------------------------

    from services.traffic.disruption_service import (
        DisruptionService,
    )

    service = DisruptionService()

    result = await service.reroute_affected_routes(
        world=world,
        incident=incident,
    )

    return {
        "success": True,
        "incident_id": incident_id,
        **result,
    }