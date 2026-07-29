# tests/integration/test_traffic_pipeline.py

import os
import osmnx as ox

from services.world.world_manager import world_manager
from services.traffic.traffic_pipeline import TrafficPipeline

CACHE_FILE = "cache/singapore.graphml"


def initialise_world():

    if not os.path.exists(CACHE_FILE):
        raise FileNotFoundError(
            f"Missing graph cache: {CACHE_FILE}"
        )

    graph = ox.load_graphml(CACHE_FILE)

    world_manager.initialise(
        graph=graph,
        vehicles=[],
    )

    return world_manager.get_world()


def test_full_traffic_pipeline():

    ########################################################
    # Arrange
    ########################################################

    world = initialise_world()

    original_edge_count = len(world.graph.edges)

    ########################################################
    # Act
    ########################################################

    pipeline = TrafficPipeline()

    world = pipeline.update()

    ########################################################
    # Assert
    ########################################################

    assert world is not None

    #
    # Traffic successfully downloaded
    #
    assert world.traffic_events is not None

    #
    # Matching completed
    #
    assert world.matched_events is not None

    #
    # Graph still exists
    #
    assert world.graph is not None

    #
    # Graph wasn't accidentally replaced
    #
    assert len(world.graph.edges) == original_edge_count

    ########################################################
    # Diagnostics
    ########################################################

    print("\n========== TRAFFIC SUMMARY ==========")
    print(f"Traffic events : {len(world.traffic_events)}")
    print(f"Matched events : {len(world.matched_events)}")

    traffic_edges = 0
    routing_cost_edges = 0
    closed_edges = 0

    for _, _, _, data in world.graph.edges(keys=True, data=True):

        if "traffic_level" in data:
            traffic_edges += 1

        if "routing_cost" in data:
            routing_cost_edges += 1

        if data.get("closed", False):
            closed_edges += 1

    print(f"Edges with traffic_level : {traffic_edges}")
    print(f"Edges with routing_cost  : {routing_cost_edges}")
    print(f"Closed edges             : {closed_edges}")
    print("=====================================\n")