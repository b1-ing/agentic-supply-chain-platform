from dataclasses import dataclass

from models.order.routing_location import RoutingLocation
from models.vehicles.vehicle import Vehicle
from models.routing.pickup_delivery_pair import PickupDeliveryPair

@dataclass(slots=True)
class RoutingProblem:

    locations: list[RoutingLocation]

    vehicles: list[Vehicle]

    starts: list[int]
    ends: list[int]

    demands: list[int]

    capacities: list[int]

    pickup_delivery_pairs: list[PickupDeliveryPair]

    @property
    def vehicle_count(self):
        return len(self.vehicles)

    @property
    def location_count(self):
        return len(self.locations)
