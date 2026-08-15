from abc import ABC
from enum import Enum
from typing import Optional

from pydantic import BaseModel
from models.routing.vehicle_route import VehicleRoute


class VehicleStatus(str, Enum):
    IDLE = "IDLE"
    EN_ROUTE = "EN_ROUTE"
    LOADING = "LOADING"
    OFFLINE = "OFFLINE"


class Vehicle(BaseModel, ABC):
    vehicle_id: str
    status: VehicleStatus = VehicleStatus.IDLE

    current_route_id: str | None = None

    route_progress_m: float = 0.0

    depot_id: str

    current_node: Optional[int] = None
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None

    current_route: VehicleRoute | None = None

    max_weight_kg: float

    height_m: float
    width_m: float
    length_m: float

    refrigerated: bool = False
    fragile_capable: bool = False
    hazardous_certified: bool = False
