from pydantic import BaseModel


class OrderResponse(BaseModel):
    order_id: str

    pickup_address: str
    delivery_address: str

    pickup_lat: float | None = None
    pickup_lon: float | None = None

    delivery_lat: float | None = None
    delivery_lon: float | None = None

    pickup_node: int | None = None
    delivery_node: int | None = None

    height_m: float | None = None
    weight_kg: float | None = None
    volume_m3: float | None = None
    pallets: int | None = None

    refrigerated: bool
    hazardous: bool
    fragile: bool
    oversized: bool

    earliest_pickup: str | None = None
    latest_pickup: str | None = None

    earliest_delivery: str | None = None
    latest_delivery: str | None = None

    assigned_vehicle: str | None = None

    notes: str | None = None