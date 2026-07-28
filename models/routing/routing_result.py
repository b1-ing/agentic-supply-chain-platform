from dataclasses import dataclass


@dataclass
class RoutingResult:

    geometry: list[tuple[float, float]]

    travel_time: float

    distance: float

    instructions: list