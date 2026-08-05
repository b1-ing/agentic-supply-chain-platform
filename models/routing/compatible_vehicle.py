from dataclasses import dataclass
from models.vehicles.vehicle import VehicleStatus
@dataclass
class CompatibleVehicle:
    vehicle_id: str
    status: VehicleStatus
    remaining_route_minutes: float
    remaining_capacity_kg: float
