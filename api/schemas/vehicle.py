from pydantic import BaseModel


class VehicleResponse(BaseModel):
    vehicle_id: str
    status: str

    current_node: int | None = None
    current_lat: float | None = None
    current_lon: float | None = None

    max_weight_kg: float
    max_volume_m3: float
    max_pallets: int

    height_m: float
    width_m: float
    length_m: float

    refrigerated: bool
    hazardous_certified: bool

    current_route_id: str | None = None