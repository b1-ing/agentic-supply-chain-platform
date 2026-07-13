from dataclasses import dataclass


@dataclass(slots=True)
class RouteSegment:
    from_node: int
    to_node: int

    graph_path: list[int]

    geometry: list[tuple[float, float]]

    travel_time: float
    distance: float