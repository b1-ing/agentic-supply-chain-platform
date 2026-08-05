from dataclasses import dataclass

@dataclass
class IncompatibleVehicle:
    vehicle_id: str
    reason: str