from dataclasses import dataclass


@dataclass(slots=True)
class RouteSegment:
    nodes: list[int]

    geometry: list[tuple[float, float]]

    distance: float

    travel_time: float

    instructions: list | None = None
