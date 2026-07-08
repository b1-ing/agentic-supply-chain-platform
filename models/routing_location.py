# models/routing_location.py

from dataclasses import dataclass
from typing import Literal


@dataclass(slots=True)
class RoutingLocation:
    """
    Represents a location that participates in routing.
    The order of these objects defines the rows/columns
    of the travel matrix.
    """

    id: str
    graph_node: int

    location_type: Literal[
        "depot",
        "pickup",
        "delivery",
        "vehicle_start",
        "vehicle_end",
    ]