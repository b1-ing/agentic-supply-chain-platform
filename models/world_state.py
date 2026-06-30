# models/world_state.py

from dataclasses import dataclass, field
import networkx as nx

from models.events import TrafficIncident
# from models.vehicle import Vehicle
# from models.mission import Mission


@dataclass
class WorldState:
    graph: nx.MultiDiGraph

    traffic_events: list[TrafficIncident] = field(default_factory=list)

    matched_events: list = field(default_factory=list)

#     vehicles: list[Vehicle] = field(default_factory=list)

#     missions: list[Mission] = field(default_factory=list)

    assessments: list = field(default_factory=list)

    constraints: list = field(default_factory=list)

    routes: list = field(default_factory=list)
