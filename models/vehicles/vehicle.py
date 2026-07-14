from abc import ABC
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class VehicleStatus(str, Enum):
    IDLE = "IDLE"
    EN_ROUTE = "EN_ROUTE"
    LOADING = "LOADING"
    OFFLINE = "OFFLINE"


class Vehicle(BaseModel, ABC):
    vehicle_id: str
    status: VehicleStatus = VehicleStatus.IDLE

    current_node: Optional[int] = None
    current_lat: Optional[float] = None
    current_lon: Optional[float] = None

    max_weight_kg: float
    max_volume_m3: float
    max_pallets: int

    height_m: float
    width_m: float
    length_m: float

    refrigerated: bool = False
    hazardous_certified: bool = False
