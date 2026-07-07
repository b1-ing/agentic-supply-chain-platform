from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class IncomingOrder(BaseModel):
    """Order extracted from natural language."""

    pickup_address: str = Field(
        description="Pickup address or location."
    )

    delivery_address: str = Field(
        description="Delivery address or location."
    )

    weight_kg: Optional[float] = Field(
        default=None,
        description="Weight in kilograms."
    )

    volume_m3: Optional[float] = Field(
        default=None,
        description="Cargo volume in cubic metres."
    )

    pallets: Optional[int] = Field(
        default=None,
        description="Number of pallets."
    )

    refrigerated: Optional[bool] = Field(
        default=None,
        description="Whether refrigerated transport is required."
    )

    hazardous: Optional[bool] = Field(
        default=None,
        description="Whether the cargo is hazardous."
    )

    fragile: Optional[bool] = Field(
        default=None,
        description="Whether the cargo is fragile."
    )

    oversized: Optional[bool] = Field(
        default=None,
        description="Whether the cargo is oversized."
    )

    earliest_pickup: Optional[str] = None
    latest_pickup: Optional[str] = None
    earliest_delivery: Optional[str] = None
    latest_delivery: Optional[str] = None

    notes: Optional[str] = Field(
        default=None,
        description="Additional customer instructions."
    )