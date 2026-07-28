# models/travel_matrix.py

from dataclasses import dataclass

import numpy as np

from models.order.routing_location import RoutingLocation


@dataclass(slots=True)
class TravelMatrix:
    """
    Pairwise travel-time matrix.

    matrix[i][j] is the travel time from
    locations[i] -> locations[j].
    """

    matrix: np.ndarray
    locations: list[RoutingLocation]
