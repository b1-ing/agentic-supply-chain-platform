from dataclasses import dataclass, field

from models.vehicle_route import VehicleRoute


@dataclass(slots=True)
class RoutePlan:
    routes: list[VehicleRoute] = field(default_factory=list)

    total_distance: float = 0
    total_travel_time: float = 0
