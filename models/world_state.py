# models/world_state.py

from dataclasses import dataclass, field
import networkx as nx

from models.events import TrafficIncident
# from models.vehicle import Vehicle
# from models.mission import Mission


@dataclass
class WorldState:
    # 1. Non-default arguments MUST go at the very top
    graph: nx.MultiDiGraph = None
    mapping: Dict = None

    # 2. Sequential lists initializing with factories
    traffic_events: list[TrafficIncident] = field(default_factory=list)
    matched_events: list = field(default_factory=list)

    # vehicles: list[Vehicle] = field(default_factory=list)
    # missions: list[Mission] = field(default_factory=list)

    assessments: list = field(default_factory=list)
    constraints: list = field(default_factory=list)
    routes: list = field(default_factory=list)


    # 3. Primitive fields using the correct type annotation syntax with default values
    recommend_replan: bool = False
    summary: str = ""


