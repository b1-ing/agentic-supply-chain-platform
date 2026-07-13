from dataclasses import dataclass
from typing import Literal


@dataclass(slots=True)
class RoutingLocation:
    matrix_index: int

    graph_node: int

    lat: float
    lon: float

    kind: Literal[
        "depot",
        "pickup",
        "delivery",
    ]

    order_id: str | None = None
    vehicle_id: str | None = None