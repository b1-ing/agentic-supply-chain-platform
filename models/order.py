from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class Order(BaseModel):
    order_id: Optional[str] = None

    customer_id: Optional[str] = None

    priority: int = 1

    status: str = "PENDING"

    pickup_address: str
    delivery_address: str

    weight_kg: Optional[float] = None
    volume_m3: Optional[float] = None
    pallets: Optional[int] = None

    refrigerated: Optional[bool] = None
    hazardous: Optional[bool] = None
    fragile: Optional[bool] = None
    oversized: Optional[bool] = None

    vehicle_class: Optional[str] = None

    earliest_pickup: Optional[datetime] = None
    latest_pickup: Optional[datetime] = None
    earliest_delivery: Optional[datetime] = None
    latest_delivery: Optional[datetime] = None

    notes: str = ""
