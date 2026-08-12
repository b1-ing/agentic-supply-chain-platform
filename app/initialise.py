# app/initialise.py

import osmnx as ox
from pathlib import Path
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
    print("[*] Initializing OpenStreetMap environment for Singapore...")
    graph_file_path = Path("cache/singapore.graphml")
    if graph_file_path.is_file():
        graph = ox.graph = ox.load_graphml(filepath=graph_file_path)
    else:
        ox.settings.useful_tags_way.extend(
            [
                "maxheight",  # Max vehicle height allowed
                "maxweight",  # Max vehicle weight allowed
                "maxwidth",  # Max vehicle width allowed
                "bridge",  # Indicates if edge is a bridge ('yes' or 'no')
                "lanes",  # Number of lanes on the roadway
            ]
        )
        graph = ox.graph_from_place("Singapore", network_type="drive")
        graph = ox.add_edge_speeds(graph)
        graph = ox.add_edge_travel_times(graph)
        ox.save_graphml(graph, filepath="cache/singapore.graphml")

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

    print(f"[Initialise] {len(world.vehicles)} vehicles loaded.")

    return world
