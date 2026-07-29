# test_pipeline.py
import os
import osmnx as ox
from services.lta_service import LTADataMallClient
from services.traffic_service import TrafficService
from traffic.road_matcher import RoadMatcher

CACHE_FILE_PATH = "cache/singapore.graphml"


def run_integration_test():
    # 1. Verify and Load the Map Graph Cache
    if not os.path.exists(CACHE_FILE_PATH):
        print(
            f"[-] Missing cache file: {CACHE_FILE_PATH}. Run your OSM download script first."
        )
        return

    print("[*] Loading cached Singapore Street Network Graph...")
    graph = ox.load_graphml(CACHE_FILE_PATH)
    print(f"[+] Map Graph loaded successfully ({len(graph.nodes)} intersections).")

    # 2. Fetch Live Incidents from LTA DataMall
    print("\n[*] Fetching live traffic incidents from LTA...")
    client = LTADataMallClient()
    service = TrafficService(client)
    incidents = service.fetch_live_incidents()

    if not incidents:
        print(
            "[-] No live incidents active right now. Cannot test matching coordinates."
        )
        return

    print(f"[+] Retracted {len(incidents)} active traffic disruptions.")
    print("=" * 60)

    # 3. Initialize RoadMatcher
    matcher = RoadMatcher(graph)

    # 4. Process and Match Incidents to the Map Network
    # We will test the first 3 incidents to keep console output clean
    for idx, incident in enumerate(incidents[:3], 1):
        print(f"\n[Incident #{idx}] Type: {incident.incident_type}")
        print(f"  Message:    {incident.message}")
        print(f"  Coordinate: ({incident.latitude}, {incident.longitude})")

        try:
            # Test Version 1: nearest_edge
            nearest_edge = matcher.nearest_edge(incident.latitude, incident.longitude)

            # Test Version 2: nearby_edges (currently returns a list containing nearest)
            nearby_list = matcher.nearby_edges(
                incident.latitude, incident.longitude, radius=100
            )

            print(f"  -> nearest_edge: {nearest_edge}")
            print(f"  -> nearby_edges: {nearby_list}")
            print(
                f"  [Match Status] Linked to OpenStreetMap nodes: From {nearest_edge[0]} to {nearest_edge[1]}"
            )

        except Exception as e:
            print(f"  [-] Matching Failed: {e}")
            print(
                "  💡 Tip: If this fails, the coordinate might be slightly outside your saved cache boundary."
            )

    print("\n" + "=" * 60)
    print("[+] Test Completed.")


if __name__ == "__main__":
    run_integration_test()
