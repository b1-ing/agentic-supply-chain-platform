from dataclasses import dataclass

from models.routing_location import RoutingLocation
from models.vehicles.vehicle import Vehicle


@dataclass(slots=True)
class RoutingProblem:
    """
    Complete optimization problem to be solved by OR-Tools.
    """

    locations: list[RoutingLocation]

    vehicles: list[Vehicle]

    starts: list[int]
    ends: list[int]

    demands: list[int]

    capacities: list[int]

    pickup_delivery_pairs: list[tuple[int, int]]


    @property
    def vehicle_count(self) -> int:
        return len(self.vehicles)

    @property
    def location_count(self) -> int:
        return len(self.locations)