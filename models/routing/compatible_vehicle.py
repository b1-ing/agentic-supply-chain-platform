from dataclasses import dataclass
from models.vehicles.vehicle import VehicleStatus


@dataclass(slots=True)
class CompatibleVehicle:
    vehicle_id: str
    status: str
    current_node: int | None

    remaining_capacity_kg: float

    remaining_route_minutes: float

    distance_to_pickup_minutes: float | None
