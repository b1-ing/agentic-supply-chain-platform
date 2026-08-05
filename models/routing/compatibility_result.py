from dataclasses import dataclass
from models.routing.compatible_vehicle import CompatibleVehicle
from models.routing.incompatible_vehicle import IncompatibleVehicle


@dataclass
class CompatibilityResult:
    order_id: str

    compatible: list[CompatibleVehicle]

    incompatible: list[IncompatibleVehicle]