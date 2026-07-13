from pathlib import Path
import numpy as np
import osmnx as ox
import pandas as pd

from models.routing_location import RoutingLocation
from routing.matrix_service import MatrixService


class World:
    """Mock wrapper around the networkx graph required by MatrixService."""

    def __init__(self, graph):
        self.graph = graph


def load_or_download_singapore_graph() -> ox.graph:
    print("[*] Initializing OpenStreetMap environment for Singapore...")

    cache_dir = Path("cache")
    cache_dir.mkdir(exist_ok=True)
    graph_file_path = cache_dir / "singapore.graphml"

    if graph_file_path.is_file():
        print(f"[+] Loading cached graph from {graph_file_path}...")
        graph = ox.load_graphml(filepath=graph_file_path)
    else:
        print(
            "[!] Cache miss. Downloading Singapore road network (this may take a few minutes)..."
        )
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
        print("[*] Imputing edge speeds and calculating travel times...")
        graph = ox.add_edge_speeds(graph)
        graph = ox.add_edge_travel_times(graph)

        ox.save_graphml(graph, filepath=graph_file_path)
        print(f"[+] Successfully cached graph to {graph_file_path}")

    return graph


def main():
    # 1. Get the real Singapore driving graph
    graph = load_or_download_singapore_graph()
    world = World(graph)

    # 2. Pick sample nodes from Singapore (let's pick 5 spaced out across the graph)
    all_nodes = list(graph.nodes)
    step = len(all_nodes) // 5
    sample_node_ids = [all_nodes[i * step] for i in range(5)]

    # Mapping our sample nodes to valid RoutingLocation types
    types = ["depot", "pickup", "delivery", "vehicle_start", "vehicle_end"]

    # 3. Create RoutingLocation instances matching your dataclass specification
    locations = [
        RoutingLocation(
            id=f"loc_{i:03d}",
            graph_node=node_id,
            location_type=types[i],  # Cycle through your Literal types
        )
        for i, node_id in enumerate(sample_node_ids)
    ]

    # Print out our configured routing locations for visibility
    print("\n[*] Initialized Locations:")
    for loc in locations:
        print(
            f"  - ID: {loc.id} | Node: {loc.graph_node:<10} | Type: {loc.location_type}"
        )

    # 4. Generate the matrix using your actual service
    print(f"\n[*] Running MatrixService over {len(locations)} locations...")
    service = MatrixService()
    travel_matrix_result = service.build(world, locations)

    # 5. Format and display the results
    # Converting default travel_time (seconds) into minutes for easier readability
    matrix_in_minutes = travel_matrix_result.matrix / 60.0

    # Row and Column labels mapped cleanly by your location IDs
    loc_labels = [f"{loc.id} ({loc.location_type})" for loc in locations]
    df = pd.DataFrame(matrix_in_minutes, index=loc_labels, columns=loc_labels)

    print("\n=== Travel Time Matrix for Singapore (in Minutes) ===")
    print(df.round(2).to_string())
    print("=====================================================")


if __name__ == "__main__":
    main()
