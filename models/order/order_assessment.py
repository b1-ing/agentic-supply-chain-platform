from __future__ import annotations

from pydantic import BaseModel, Field


class InferredConstraint(BaseModel):
    type: str = Field(
        description=(
            "Operational constraint type, e.g. "
            "avoid_congestion, minimize_travel_time, "
            "avoid_area, minimize_stops, require_refrigeration."
        )
    )

    value: str | float | int | bool | None = None

    priority: str = Field(
        default="medium",
        description="low, medium, high, or critical",
    )

    hard: bool = Field(
        default=False,
        description=(
            "Whether this is an absolute requirement rather than "
            "a preference."
        ),
    )

    reason: str = Field(
        description="Why this constraint was inferred from the order."
    )


class OrderAssessment(BaseModel):
    pickup_address: str | None = None
    delivery_address: str | None = None

    weight_kg: float | None = None


    height_m: float | None = None
    width_m: float | None = None
    length_m: float | None = None

    refrigerated: bool = False
    hazardous: bool = False
    fragile: bool = False
    oversized: bool = False

    earliest_pickup: str | None = None
    latest_pickup: str | None = None
    earliest_delivery: str | None = None
    latest_delivery: str | None = None

    constraints: list[InferredConstraint] = Field(
        default_factory=list
    )

    missing_information: list[str] = Field(
        default_factory=list
    )

    ambiguities: list[str] = Field(
        default_factory=list
    )