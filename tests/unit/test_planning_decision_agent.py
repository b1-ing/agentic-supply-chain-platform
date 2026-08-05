import asyncio
import networkx as nx

from agents.planning.planning_decision_agent import PlanningDecisionAgent

from models.world_state import WorldState
from models.depot import Depot
from models.incoming_state import IncomingOrder

from models.vehicles.standard_truck import StandardTruck
from models.vehicles.refrigerated_truck import RefrigeratedTruck
from models.vehicles.tall_truck import TallTruck


def build_graph():

    G = nx.MultiDiGraph()

    coordinates = {
        0: (103.800, 1.300),
        1: (103.801, 1.301),
        2: (103.802, 1.302),
        3: (103.803, 1.303),
        4: (103.804, 1.304),
    }

    for node, (lon, lat) in coordinates.items():
        G.add_node(
            node,
            x=lon,
            y=lat,
        )

    edges = [
        (0, 1),
        (1, 0),
        (1, 2),
        (2, 1),
        (2, 3),
        (3, 2),
        (3, 4),
        (4, 3),
        (4, 0),
        (0, 4),
    ]

    for u, v in edges:
        G.add_edge(
            u,
            v,
            travel_time=5,
            length=100,
        )

    return G


async def run_test():

    graph = build_graph()

    world = WorldState(
        graph=graph,
        depots=[
            Depot(
                depot_id="HQ",
                graph_node=0,
                lat=1.300,
                lon=103.800,
            )
        ],
        vehicles=[
            StandardTruck(vehicle_id="TRUCK-001"),
            RefrigeratedTruck(vehicle_id="COLD-001"),
            TallTruck(vehicle_id="TALL-001"),
        ],
        new_orders=[],
        orders_in_progress=[
            IncomingOrder(
                order_id="ORDER-001",
                pickup_address="Jurong",
                delivery_address="Changi",
                pickup_node=1,
                delivery_node=3,
                weight_kg=20,
            ),
            IncomingOrder(
                order_id="ORDER-002",
                pickup_address="Tuas",
                delivery_address="Woodlands",
                pickup_node=2,
                delivery_node=4,
                weight_kg=40,
                refrigerated=True,
            ),
        ],
    )

    agent = PlanningDecisionAgent()

    decision = await agent.run(world)

    print("\n========== LLM DECISION ==========\n")
    print(decision)
    print("\n==================================\n")

    assert decision is not None


if __name__ == "__main__":
    asyncio.run(run_test())
