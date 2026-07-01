# services/tomtom_service.py

import math
import concurrent.futures
from typing import List, Dict, Tuple, Set
import requests
import networkx as nx
import mapbox_vector_tile
from shapely.geometry import shape
from shapely.strtree import STRtree

class TomTomTileService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.zoom = 10  # Set to Zoom 12 to match your working link footprint
        self.base_url = "https://api.tomtom.com/traffic/map/4/tile/flow/relative"

    def lat_lon_to_tile_xyz(self, lat: float, lon: float) -> Tuple[int, int]:
        """Converts coordinates directly into standard Web Mercator grid indexes."""
        lat_rad = math.radians(lat)
        n = 2.0 ** self.zoom
        x_tile = int((lon + 180.0) / 360.0 * n)
        y_tile = int((1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi) / 2.0 * n)
        return x_tile, y_tile

    def get_required_tiles_for_graph(self, graph: nx.MultiDiGraph) -> Set[Tuple[int, int]]:
        """Maps active graph nodes to their corresponding unique tile IDs."""
        tiles = set()
        for _, node_data in graph.nodes(data=True):
            lat, lon = node_data.get("y"), node_data.get("x")
            if lat and lon:
                x, y = self.lat_lon_to_tile_xyz(lat, lon)
                tiles.add((x, y))
        return tiles

    def fetch_single_tile(self, x: int, y: int) -> List[Dict]:
        """Downloads a single tile and projects local tile vectors into standard global coordinates."""
        literal_url = (
            f"{self.base_url}/{self.zoom}/{x}/{y}.pbf"
            f"?margin=0.1"
            f"&tags=%5Btraffic_level,traffic_road_coverage,left_hand_traffic,road_closure,road_category,road_subcategory%5D"
            f"&key={self.api_key}"
        )

        headers = {"accept": "*/*"}

        try:
            response = requests.get(literal_url, headers=headers, timeout=10)

            if response.status_code == 204:
                return []
            if response.status_code != 200:
                return []

            # -----------------------------------------------------------------
            # FIX: Force decoding to re-project into global Lat/Lon coordinates
            # -----------------------------------------------------------------
            decoded_tile = mapbox_vector_tile.decode(
                response.content,
                y_coord_down=True,  # Matches TomTom's Web Mercator orientation
                transformer=lambda px, py: self.tile_pixel_to_lng_lat(x, y, px, py)
            )

            flow_layer = decoded_tile.get("Traffic flow", decoded_tile.get("flow", {}))

            segments = []
            for feature in flow_layer.get("features", []):
                properties = feature.get("properties", {})

                segments.append({
                    "traffic_level": properties.get("traffic_level", 0.0),
                    "closed": properties.get("road_closure", False),
                    "geometry": shape(feature.get("geometry"))  # Now a valid decimal shape!
                })
            return segments

        except Exception as e:
            print(f"[-] Error decoding tile {x},{y}: {e}")
            return []

    def tile_pixel_to_lng_lat(self, tile_x: int, tile_y: int, px: float, py: float, extent: int = 4096) -> Tuple[float, float]:
        """Mathematical conversion transforming local tile points back to global web mercator points."""
        n = 2.0 ** self.zoom
        # Calculate coordinate boundaries for this specific tile square footprint
        lon_left = (tile_x / n) * 360.0 - 180.0
        lon_right = ((tile_x + 1) / n) * 360.0 - 180.0

        lat_rad_top = math.atan(math.sinh(math.pi * (1.0 - 2.0 * tile_y / n)))
        lat_rad_bottom = math.atan(math.sinh(math.pi * (1.0 - 2.0 * (tile_y + 1) / n)))

        lat_top = math.degrees(lat_rad_top)
        lat_bottom = math.degrees(lat_rad_bottom)

        # Interpolate exact pixel offset position within the tile grid bounds
        lon = lon_left + (px / extent) * (lon_right - lon_left)
        lat = lat_top - (py / extent) * (lat_top - lat_bottom)

        return lon, lat
    def fetch_all_tiles_concurrently(self, tile_coords: Set[Tuple[int, int]]) -> List[Dict]:
        all_segments = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_tile = {executor.submit(self.fetch_single_tile, x, y): (x, y) for x, y in tile_coords}
            for future in concurrent.futures.as_completed(future_to_tile):
                all_segments.extend(future.result())
        return all_segments

    def sync_network_flow(self, graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """Updates graph routing costs using an accelerated spatial index lookup."""
        needed_tiles = self.get_required_tiles_for_graph(graph)
        print(f"[*] Map Display v4 Sync: Requesting tiles: {needed_tiles} at Zoom Level {self.zoom}...")

        if not needed_tiles:
            return graph

        traffic_segments = self.fetch_all_tiles_concurrently(needed_tiles)
        print(f"[+] Successfully parsed {len(traffic_segments)} active geometric vector features.")

        if not traffic_segments:
            return graph

        graph_edges = []
        edge_references = []
        for u, v, k, edge_data in graph.edges(keys=True, data=True):
            if "geometry" in edge_data:
                graph_edges.append(edge_data["geometry"])
                edge_references.append((u, v, k, edge_data))

        if not graph_edges:
            print("[-] Error: Graph edges are missing geometry elements.")
            return graph

        spatial_tree = STRtree(graph_edges)
        matching_tolerance_degrees = 0.0005
        updated_count = 0

        for segment in traffic_segments:
            segment_geom = segment["geometry"]

            # Find any edges whose bounding envelopes overlap with our traffic line segment
            buffered_segment = segment_geom.buffer(matching_tolerance_degrees)
            candidate_indices = spatial_tree.query(buffered_segment)

            for idx in candidate_indices:
                u, v, k, edge_data = edge_references[idx]
                edge_line = graph_edges[idx]

                # Verify that the traffic line closely shares a path with the road edge
                if edge_line.intersects(buffered_segment) or edge_line.distance(segment_geom) <= matching_tolerance_degrees:

                    # ---------------------------------------------------------
                    # FIX: Explicitly assign the traffic level variable here!
                    # ---------------------------------------------------------
                    edge_data["traffic_level"] = segment["traffic_level"]

                    if segment["closed"]:
                        edge_data["closed"] = True
                        edge_data["routing_cost"] = float("inf")
                    elif segment["traffic_level"] > 0:
                        base_time = edge_data.get("travel_time", 1.0)
                        penalty_multiplier = min(5.0, 1.0 + (segment["traffic_level"] * 3.0))
                        edge_data["routing_cost"] = base_time * penalty_multiplier
                    else:
                        # Ensure clear roads map cleanly
                        edge_data["routing_cost"] = edge_data.get("travel_time", 1.0)

                    updated_count += 1
                    break  # Match confirmed, move to the next segment

        print(f"[+] Sync finished. Processed updates across {updated_count} network edges.")
        return graph