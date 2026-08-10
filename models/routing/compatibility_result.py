from dataclasses import dataclass
from models.routing.compatible_vehicle import CompatibleVehicle
from models.routing.incompatible_vehicle import IncompatibleVehicle
from enum import Enum

class CompatibilityStatus(Enum):

    ROUTABLE = "ROUTABLE"

    WAITING = "WAITING"

    UNSERVICEABLE = "UNSERVICEABLE"


@dataclass
class CompatibilityResult:

    order_id: str

    compatible: list[CompatibleVehicle]

    incompatible: list[IncompatibleVehicle]

    allowed_vehicle_indices: list[int]

    status: CompatibilityStatus