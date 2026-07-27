from dataclasses import dataclass


@dataclass(kw_only=True)
class Depot:
    depot_id: str
    graph_node: int
    lat: float
    lon: float
