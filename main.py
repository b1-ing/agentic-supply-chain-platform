# main.py

import osmnx as ox
import folium
import math
from models.world_state import WorldState
from services.osm_service import OSMService
from services.tomtom_service import TomTomTileService
from workflow.graph import build_workflow
import os

from utils.matrix_generator import generate_cvrp_time_matrix
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def solve_cvrp(time_matrix: list, num_vehicles: int, depot_index: int):
    """Standard Google OR-Tools CVRP Execution Loop."""
    print("[*] Instantiating Google OR-Tools CVRP Solver Engine...")

    # Create the routing index manager
    manager = pywrapcp.RoutingIndexManager(len(time_matrix), num_vehicles, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    # Define the cost callback (Traffic-adjusted time)
    def time_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return int(time_matrix[from_node][to_node] * 60) # Convert minutes to seconds for integer solver

    transit_callback_index = routing.RegisterTransitCallback(time_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Set search parameters
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    # Solve the problem
    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        print("[+] Success! Traffic-optimized routing path solved.")
        # (Add your path printing layout code here as needed)
    else:
        print("[-] Solver failed to locate a valid routing path.")

def draw_tile_grid(m, bbox, zoom):
    """Calculates and draws the boundaries of the TomTom XYZ tiles."""
    min_lat, max_lat, min_lon, max_lon = bbox

    def get_tile_frac(lat, lon, z):
        lat_rad = math.radians(lat)
        n = 2.0 ** z
        x = (lon + 180.0) / 360.0 * n
        y = (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n
        return x, y

    def tile_to_lat_lon(x, y, z):
        n = 2.0 ** z
        lon = x / n * 360.0 - 180.0
        lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
        lat = math.degrees(lat_rad)
        return lat, lon

    x_min, y_max = get_tile_frac(min_lat, min_lon, zoom)
    x_max, y_min = get_tile_frac(max_lat, max_lon, zoom)

    start_x, end_x = int(x_min), int(x_max)
    start_y, end_y = int(min(y_min, y_max)), int(max(y_min, y_max))

    tile_group = folium.FeatureGroup(name=f"TomTom Tiles (Zoom {zoom})", show=True)

    for tx in range(start_x, end_x + 1):
        for ty in range(start_y, end_y + 1):
            nw_lat, nw_lon = tile_to_lat_lon(tx, ty, zoom)
            se_lat, se_lon = tile_to_lat_lon(tx + 1, ty + 1, zoom)
            bounds = [[se_lat, nw_lon], [nw_lat, se_lon]]

            folium.Rectangle(
                bounds=bounds,
                color="#00FFFF",
                weight=2,
                fill=True,
                fill_color="#00FFFF",
                fill_opacity=0.03,
                popup=f"<b>Tile Address</b><br>Zoom: {zoom}<br>X: {tx}<br>Y: {ty}"
            ).add_to(tile_group)

            center_lat = (nw_lat + se_lat) / 2
            center_lon = (nw_lon + se_lon) / 2
            folium.map.Marker(
                [center_lat, center_lon],
                icon=folium.DivIcon(
                    html=f'<div style="font-size: 10px; color: #00FFFF; font-weight: bold; background: rgba(0,0,0,0.5); padding: 2px; border-radius: 3px; width: 80px; text-align: center;">X:{tx}, Y:{ty}</div>'
                )
            ).add_to(tile_group)

    return tile_group


def create_combined_dashboard(world_state, zoom_level=12):
    """Generates an interactive Leaflet map overlaying tiles and graph costs."""
    graph = world_state.graph

    m = folium.Map(location=[1.3521, 103.8198], zoom_start=11, tiles="cartodbpositron")

    lats = [d["y"] for n, d in graph.nodes(data=True)]
    lons = [d["x"] for n, d in graph.nodes(data=True)]
    bbox = (min(lats), max(lats), min(lons), max(lons))

    tile_grid_layer = draw_tile_grid(m, bbox, zoom_level)
    tile_grid_layer.add_to(m)

    graph_edges_layer = folium.FeatureGroup(name="NetworkX Road Graph", show=True)

    for u, v, k, data in graph.edges(keys=True, data=True):
        cost = data.get("routing_cost", data.get("travel_time", 0))
        base_time = data.get("travel_time", 0)
        traffic_level = data.get("traffic_level", 0.0)

        if "geometry" in data:
            coords = [(p[1], p[0]) for p in data["geometry"].coords]
        else:
            coords = [(graph.nodes[u]["y"], graph.nodes[u]["x"]), (graph.nodes[v]["y"], graph.nodes[v]["x"])]

        # -----------------------------------------------------------------
        # TOMTOM COLOURED TRAFFIC STATUS SCHEME
        # -----------------------------------------------------------------
        if data.get("closed") or cost == float("inf"):
            color = "#111111"       # Charcoal / Black -> Road Closed
            weight = 4.5
        elif traffic_level >= 0.80:
            color = "#810000"       # Dark Burgundy -> Heavy Gridlock
            weight = 4.0
        elif traffic_level >= 0.40:
            color = "#E21818"       # Bright Red -> Congested Delays
            weight = 3.5
        elif traffic_level >= 0.15:
            color = "#FFA117"       # Orange -> Moderate Slowdowns
            weight = 2.5
        else:
            color = "#00D26A"       # Vibrant Green -> Free Flow
            weight = 1.5

        popup_text = (
            f"<b>Edge:</b> {u} &rarr; {v}<br>"
            f"<b>Base Time:</b> {base_time:.2f} mins<br>"
            f"<b>Current Cost:</b> {cost:.2f} mins<br>"
            f"<b>Congestion Factor:</b> {traffic_level * 100:.1f}%"
        )

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=weight,
            opacity=0.85,
            popup=popup_text
        ).add_to(graph_edges_layer)

    graph_edges_layer.add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    m.save("singapore_tiles_dashboard.html")
    print("[*] Dashboard compiled! Open 'singapore_tiles_dashboard.html' in your browser to inspect.")


# =====================================================================
# CORE EXECUTION PIPELINE
# =====================================================================
if __name__ == "__main__":
    print("[*] Initializing OpenStreetMap environment for Singapore...")
    osm = OSMService()
    graph = osm.load_graph("Singapore")
    graph = ox.add_edge_speeds(graph)
    graph = ox.add_edge_travel_times(graph)

    print("[*] Contacting TomTom Traffic flow stream...")
    # Clean fallback check for missing environment key variables
    api_key = os.getenv("TOMTOM_API_KEY")
    if not api_key:
        raise ValueError("Missing TOMTOM_API_KEY inside your local environment variable stack.")

    # Initialize service which locks back-end pulls to Zoom 12
    tomtom = TomTomTileService(api_key=api_key)
    graph = tomtom.sync_network_flow(graph)

    # =====================================================================
    # DIAGNOSTIC CHECK: VERIFY TRAFFIC PROPAGATION
    # =====================================================================
    print("\n" + "="*50)
    print("[*] RUNNING TRAFFIC DATA INVENTORY CHECK...")
    print("="*50)

    total_edges = 0
    edges_with_traffic_level = 0
    edges_with_routing_cost = 0
    congested_edges_count = 0
    closed_edges_count = 0

    for u, v, k, data in graph.edges(keys=True, data=True):
        total_edges += 1

        # Check if the attribute exists at all
        if "traffic_level" in data:
            edges_with_traffic_level += 1
            if data["traffic_level"] > 0:
                congested_edges_count += 1

        if "routing_cost" in data:
            edges_with_routing_cost += 1

        if data.get("closed") or data.get("routing_cost") == float("inf"):
            closed_edges_count += 1

    print(f"[>] Total NetworkX Edges Evaluated:   {total_edges}")
    print(f"[>] Edges with 'traffic_level' key:   {edges_with_traffic_level}")
    print(f"[>] Edges with 'routing_cost' key:    {edges_with_routing_cost}")
    print(f"[>] Edges with Active Traffic (> 0):   {congested_edges_count}")
    print(f"[>] Edges marked Closed (Blocked):     {closed_edges_count}")
    print("="*50 + "\n")
    # =====================================================================

    # Wrap inside the state channel dataclass container
    world = WorldState(graph=graph)

    print("[*] Executing LangGraph intelligent optimization nodes...")
    workflow = build_workflow()
    result = workflow.invoke({"world": world})

    # Output structural data logs to console
    print("\n[+] Extraction Verification:")
    print(result["world"].constraints)

    optimized_graph = result["world"].graph

    # Define your delivery locations (Lat, Lon)
    # Index 0 will serve as your Depot/Distribution Warehouse
    delivery_points = [
        (1.3521, 103.8198),  # Depot (Singapore Center)
        (1.3214, 103.7468),  # Customer 1 (Jurong East)
        (1.4368, 103.8315),  # Customer 2 (Yishun)
        (1.3559, 103.9870)   # Customer 3 (Changi Airport)
    ]

    # Generate the N x N Matrix
    traffic_cvrp_matrix = generate_cvrp_time_matrix(optimized_graph, delivery_points)

    # Execute Solver
    solve_cvrp(time_matrix=traffic_cvrp_matrix.tolist(), num_vehicles=2, depot_index=0)

    # Generate the map using Zoom 12 to synchronize front-end and back-end
    print("\n[*] Spinning up the visualization dashboard engine...")
    create_combined_dashboard(result["world"], zoom_level=12)