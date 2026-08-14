from datetime import datetime
from typing import Optional
from enum import Enum
from models.routing.compatible_vehicle import CompatibleVehicle
from pydantic import BaseModel, Field
from models.order.order_constraint import OrderConstraint

class IncomingOrder(BaseModel):
    """Order extracted from natural language."""

    pickup_address: str = Field(description="Pickup address or location.")

    delivery_address: str = Field(description="Delivery address or location.")

    pickup_lat: Optional[float] = Field(
        default=None, description="latitude of the pickup location"
    )

    pickup_lon: Optional[float] = Field(
        default=None, description="longitude of the pickup location"
    )

    delivery_lat: Optional[float] = Field(
        default=None, description="latitude of the delivery location"
    )

    delivery_lon: Optional[float] = Field(
        default=None, description="longitude of the delivery location"
    )

    pickup_node: Optional[int] = None

    delivery_node: Optional[int] = None

    height_m: Optional[float] = Field(default=None, description="Height in metres.")

    weight_kg: Optional[float] = Field(default=None, description="Weight in kilograms.")

    volume_m3: Optional[float] = Field(
        default=None, description="Cargo volume in cubic metres."
    )

    pallets: Optional[int] = Field(default=None, description="Number of pallets.")

    refrigerated: Optional[bool] = Field(
        default=None, description="Whether refrigerated transport is required."
    )

    hazardous: Optional[bool] = Field(
        default=None, description="Whether the cargo is hazardous."
    )

    fragile: Optional[bool] = Field(
        default=None, description="Whether the cargo is fragile."
    )

    oversized: Optional[bool] = Field(
        default=None, description="Whether the cargo is oversized."
    )

    earliest_pickup: Optional[str] = None
    latest_pickup: Optional[str] = None
    earliest_delivery: Optional[str] = None
    latest_delivery: Optional[str] = None

    constraints: list[OrderConstraint] = Field(
                                          default_factory=list
                                      )

    order_id: Optional[str] = None

    notes: Optional[str] = Field(
        default=None, description="Additional customer instructions."
    )

    assigned_vehicle: Optional[str] = Field(
        default=None, description="Vehicle assigned to this order."
    )


class OrderStatus(Enum):
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    PICKED_UP = "PICKED_UP"
    DELIVERING = "DELIVERING"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    UNSERVICEABLE = "UNSERVICEABLE"
