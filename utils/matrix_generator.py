# utils/matrix_generator.py

import networkx as nx
import numpy as np
from typing import List, Dict, Tuple


def generate_cvrp_time_matrix(
    graph: nx.MultiDiGraph, locations: List[Tuple[float, float]]
) -> np.ndarray:
    """
    Takes a list of GPS points [(lat, lon), ...] and finds the shortest travel paths
    between all of them using the traffic-adjusted 'routing_cost' attribute.
    """
    # 1. Map your physical delivery lat/lon coordinates to the nearest OSM node IDs
    import osmnx as ox

    print("[*] Snapping delivery coordinates to the nearest road network nodes...")

    lats, lons = zip(*locations)
    node_ids = ox.nearest_nodes(graph, X=lons, Y=lats)

    num_nodes = len(node_ids)
    time_matrix = np.zeros((num_nodes, num_nodes), dtype=float)

    # 2. Compute all-pairs shortest paths using the traffic 'routing_cost' weight
    print(
        f"[*] Computing traffic-aware cost weights for a {num_nodes}x{num_nodes} matrix..."
    )
    for i, source_node in enumerate(node_ids):
        # Dijkstra's algorithm from this source node to all other nodes in the network
        lengths = nx.single_source_dijkstra_path_length(
            graph, source_node, weight="routing_cost"
        )

        for j, target_node in enumerate(node_ids):
            # Fallback to a high value if a node is disconnected, or 0 if it's the same node
            if i == j:
                time_matrix[i][j] = 0.0
            else:
                time_matrix[i][j] = lengths.get(target_node, 999999.0)

    return time_matrix
