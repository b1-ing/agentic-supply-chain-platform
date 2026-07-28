# models/world_state.py

from dataclasses import dataclass, field
import networkx as nx

from models.events import TrafficIncident
from models.order.incoming_order import IncomingOrder
from models.depot import Depot

from models.vehicles.vehicle import Vehicle
# from models.mission import Mission


@dataclass
class WorldState:
    # 1. Non-default arguments MUST go at the very top
    # depots: list[Depot]

    graph: nx.MultiDiGraph = None
    mapping: dict = None

    # 2. Sequential lists initializing with factories
    traffic_events: list[TrafficIncident] = field(default_factory=list)
    matched_events: list = field(default_factory=list)

    vehicles: list[Vehicle] = field(default_factory=list)
    # missions: list[Mission] = field(default_factory=list)

    assessments: list = field(default_factory=list)
    constraints: list = field(default_factory=list)
    routes: list = field(default_factory=list)

    new_orders: list[IncomingOrder] = field(default_factory=list)
    orders_in_progress: list[IncomingOrder] = field(default_factory=list)
    cancelled_orders: list[IncomingOrder] = field(default_factory=list)

    # 3. Primitive fields using the correct type annotation syntax with default values
    recommend_replan: bool = False
    summary: str = ""
