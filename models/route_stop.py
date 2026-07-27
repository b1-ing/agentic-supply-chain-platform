from dataclasses import dataclass

from models.routing_location import RoutingLocation


@dataclass(slots=True)
class RouteStop:
    sequence: int
    location: RoutingLocation

    arrival_time: float | None = None
    departure_time: float | None = None

    load_after_stop: int | None = None
