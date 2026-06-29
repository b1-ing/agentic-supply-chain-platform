# test_osm.py
from osm_service import OSMService
import osmnx as ox

def test_graph_loading():
    # 1. Initialize your service
    service = OSMService()

    # 2. Load a small, manageable area for quick testing
    place_name = "Singapore, SG"
    print(f"Fetching graph for: {place_name}...")
    graph = service.load_graph(place_name)

    # 3. Print basic graph metadata
    print("\n--- Graph Summary ---")
    print(type(graph))
    print(f"Number of intersections (nodes): {len(graph.nodes)}")
    print(f"Number of road segments (edges): {len(graph.edges)}")

    # 4. Plot and display the graph
    print("\nRendering graph plot...")
    fig, ax = ox.plot_graph(graph, node_size=5, node_color="blue", edge_color="gray")

if __name__ == "__main__":
    test_graph_loading()