from dataclasses import dataclass, field

from models.routing.route_segment import RouteSegment
from models.routing.route_stop import RouteStop


@dataclass(slots=True)
class VehicleRoute:
    vehicle_id: str
    route_id: str
    stops: list[RouteStop] = field(default_factory=list)
    segments: list[RouteSegment] = field(default_factory=list)

    total_distance: float = 0
    total_travel_time: float = 0


