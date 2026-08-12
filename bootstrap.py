from pathlib import Path
from services.lta_service import LTATrafficService, LTADataMallClient
from models.world_state import WorldState
import osmnx as ox
import asyncio
import os
import json


async def bootstrap():

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
                "base_travel_time",
            ]
        )
        graph = ox.graph_from_place("Singapore", network_type="drive")
        graph = ox.add_edge_speeds(graph)
        graph = ox.add_edge_travel_times(graph)
        ox.save_graphml(graph, filepath="cache/singapore.graphml")

        os.makedirs("debug", exist_ok=True)
        nodes, edges = ox.graph_to_gdfs(graph)

        nodes.to_file("debug/nodes.geojson", driver="GeoJSON")
        edges.to_file("debug/edges.geojson", driver="GeoJSON")

    lta_client = LTADataMallClient()
    lta = LTATrafficService(lta_client)
    cache_path = "cache/lta_osm_mapping.json"
    graph = await lta.sync_network_flow_async(graph, cache_path)

    mapping_cache = {}
    cache_exists = os.path.exists(cache_path)

    if cache_exists:
        print(f"[*] [Cache] Found spatial mapping cache at {cache_path}. Loading...")
    try:
        with open(cache_path, "r") as f:
            # JSON keys are always strings, so we convert edge keys back to proper types later
            mapping_cache = json.load(f)
    except Exception as e:
        print(f"[!] Failed to read cache: {e}. Recomputing spatial tree...")
        cache_exists = False

    world = WorldState(graph=graph, mapping=mapping_cache)

    return world
