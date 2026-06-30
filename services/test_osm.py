# test_osm.py
from osm_service import OSMService
import osmnx as ox


def test_graph_loading():
    service = OSMService()
    place_name = "Singapore, SG"

    print(f"Fetching graph for: {place_name}...")
    graph = service.load_graph(place_name)

    # ---- ADD THIS LINE TO SAVE YOUR CACHE ----
    # This compiles those two JSON files into a structured network file
    ox.save_graphml(graph, filepath="cache/singapore.graphml")
    print("[+] Saved compiled map to cache/singapore.graphml")
    # ------------------------------------------

    print(f"Intersections (nodes): {len(graph.nodes)}")
    print(f"Road segments (edges): {len(graph.edges)}")


if __name__ == "__main__":
    test_graph_loading()
