# app/initialise.py

import osmnx as ox

from models.world.world_state import WorldState
from models.depot import Depot

from models.vehicles.standard_truck import StandardTruck
from models.vehicles.refrigerated_truck import RefrigeratedTruck
from models.vehicles.tall_truck import TallTruck

from services.world.world_manager import world_manager


GRAPH_PATH = "cache/singapore.graphml"


def initialise_world() -> WorldState:

    ############################################################
    # Load road network
    ############################################################

    print("[Initialise] Loading Singapore graph...")

    graph = ox.load_graphml(GRAPH_PATH)

    ############################################################
    # Depot(s)
    ############################################################

    depot_lat = 1.300557
    depot_lon = 103.799389

    depot_node = ox.distance.nearest_nodes(
        graph,
        depot_lon,
        depot_lat,
    )

    depots = [
        Depot(
            depot_id="HQ",
            graph_node=depot_node,
            lat=depot_lat,
            lon=depot_lon,
        )
    ]

    ############################################################
    # Fleet
    ############################################################

    vehicles = [
        StandardTruck(
            vehicle_id="TRUCK-001",
            current_node=depot_node,
        ),
        StandardTruck(
            vehicle_id="TRUCK-002",
            current_node=depot_node,
        ),
        RefrigeratedTruck(
            vehicle_id="COLD-001",
            current_node=depot_node,
        ),
        TallTruck(
            vehicle_id="TALL-001",
            current_node=depot_node,
        ),
    ]

    ############################################################
    # Initialise singleton
    ############################################################

    world_manager.initialise(
        graph=graph,
        vehicles=vehicles,
        mapping={},
    )

    world = world_manager.get_world()

    print(
        f"[Initialise] "
        f"{graph.number_of_nodes():,} nodes | "
        f"{graph.number_of_edges():,} edges"
    )

    print(
        f"[Initialise] "
        f"{len(world.vehicles)} vehicles loaded."
    )

    return world