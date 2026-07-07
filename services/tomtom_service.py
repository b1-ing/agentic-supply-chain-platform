# services/tomtom_service.py
"""
A service class that wraps the TomTom API and returns the live traffic flow vector tiles provided by TomTom.

Main Functions
--------------------------
sync_network_flow:

Helper Functions
--------------------------
fetch_single_tile: helper function that calls the tomtom api, decodes and geocodes a single traffic vector tile into WGS 84

fetch_all_tiles_concurrently: calls a few fetch_single_tile functions in parallel to download all the required tiles

lat_lon_to_tile_xyz: Helper function to convert WGS 84 as provided by OSM to web mercator to be passed to tomtom.

get_required_tiles_for_graph:
"""

import math
import concurrent.futures
from typing import List, Dict, Tuple, Set, Optional
import requests
import networkx as nx
import mapbox_vector_tile
from shapely.geometry import shape
from shapely.strtree import STRtree
import os
from dotenv import load_dotenv

import os
import geopandas as gpd
import networkx as nx
from services.cache import TTLCache

load_dotenv()


class TomTomTileService:
    def __init__(self):
        api_key = os.getenv("TOMTOM_API_KEY")
        if not api_key:
            raise ValueError(
                "Missing TOMTOM_API_KEY inside your local environment variable stack."
            )
        self.api_key = api_key
        self.last_parsed_segments = []
        self.zoom = 14  # Set to Zoom 12 to match your working link footprint
        self.base_url = "https://api.tomtom.com/traffic/map/4/tile/flow/relative"

        # Test-only time-based cache. Disabled by setting TOMTOM_CACHE_DISABLED=1.
        # TTL is seconds; override with TOMTOM_CACHE_TTL.
        self._cache: Optional[TTLCache] = None
        if os.getenv("TOMTOM_CACHE_DISABLED", "0") != "1":
            try:
                ttl = int(os.getenv("TOMTOM_CACHE_TTL", "3600"))
            except ValueError:
                ttl = 3600
            self._cache = TTLCache("cache/tomtom", ttl_seconds=ttl)

    def lat_lon_to_tile_xyz(self, lat: float, lon: float) -> Tuple[int, int]:
        """
        Helper function to convert WGS 84 as provided by OSM to web mercator
        to be passed to tomtom.

        Args:
            lat(float): latitude of a node
            lon(float): longitude of a node

        Returns:
            x_tile, y_tile(Tuple[int, int]): a coordinate tuple in web mercator
        """
        lat_rad = math.radians(lat)
        n = 2.0**self.zoom
        x_tile = int((lon + 180.0) / 360.0 * n)
        y_tile = int(
            (1.0 - math.log(math.tan(lat_rad) + (1 / math.cos(lat_rad))) / math.pi)
            / 2.0
            * n
        )
        return x_tile, y_tile

    def get_required_tiles_for_graph(
        self, graph: nx.MultiDiGraph
    ) -> Set[Tuple[int, int]]:
        """
        Calculates which tiles are needed for download by first converting each node in
        the graph from WGS 84 to web mercator.

        Args:
            graph(nx.MultiDiGraph): the original road graph of SG

        Returns:
            tiles(Set[Tuple[int,int]): a set of coordinates to be used as input to the TomTom API
            to pull the required tiles
        """
        tiles = set()
        for _, node_data in graph.nodes(data=True):
            lat, lon = node_data.get("y"), node_data.get("x")
            if lat and lon:
                x, y = self.lat_lon_to_tile_xyz(lat, lon)
                tiles.add((x, y))
        return tiles

    def _decode_tile_bytes(self, x: int, y: int, raw: bytes) -> List[Dict]:
        """Decode raw PBF tile bytes into a list of segment dicts."""
        decoded_tile = mapbox_vector_tile.decode(
            raw,
            y_coord_down=True,  # Matches TomTom's Web Mercator orientation
            transformer=lambda px, py: self.tile_pixel_to_lng_lat(x, y, px, py),
        )

        flow_layer = decoded_tile.get("Traffic flow", decoded_tile.get("flow", {}))

        segments = []
        for feature in flow_layer.get("features", []):
            properties = feature.get("properties", {})
            segments.append(
                {
                    "traffic_level": properties.get("traffic_level", 0.0),
                    "closed": properties.get("road_closure", False),
                    "geometry": shape(feature.get("geometry")),
                }
            )
        return segments

    def fetch_single_tile(self, x: int, y: int) -> List[Dict]:
        """Fetch a single TomTom flow tile, transparently read-through cached.

        Cache key: "{zoom}/{x}/{y}". Only non-empty responses are cached.
        """
        cache_key = f"{self.zoom}/{x}/{y}"

        if self._cache is not None:
            cached_bytes = self._cache.get(cache_key)
            if cached_bytes:
                try:
                    return self._decode_tile_bytes(x, y, cached_bytes)
                except Exception as e:
                    print(f"[-] Error decoding cached tile {x},{y}: {e}")
                    # fall through to fresh fetch

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

            segments = self._decode_tile_bytes(x, y, response.content)

            if self._cache is not None and segments:
                self._cache.set(cache_key, response.content)

            return segments

        except Exception as e:
            print(f"[-] Error decoding tile {x},{y}: {e}")
            return []

    def tile_pixel_to_lng_lat(
        self, tile_x: int, tile_y: int, px: float, py: float, extent: int = 4096
    ) -> Tuple[float, float]:
        """
        Helper function to convert TomTom's Z/X/Y tile coordinate system back to WGS 84.

        Args:
            tile_x(int): x coordinate of the tile in the zoom grid
            tile_y(int): y coordinate of the tile in the zoom grid
            px(float): point along the x axis of a single grid (from 1-4096 by default)
            py(float): point along the y axis of a single grid (from 1-4096 by default)
            extent: the range of values for px and py to take (or thought of as the sampling resolution)

        Returns:
            lon(float): longitude value of point in WGS 84
            lat(float): latitude value of point in WGS 84

        """
        n = 2.0**self.zoom
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

    def fetch_all_tiles_concurrently(
        self, tile_coords: Set[Tuple[int, int]]
    ) -> List[Dict]:
        all_segments = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_to_tile = {
                executor.submit(self.fetch_single_tile, x, y): (x, y)
                for x, y in tile_coords
            }
            for future in concurrent.futures.as_completed(future_to_tile):
                all_segments.extend(future.result())
        return all_segments

    def sync_network_flow(self, graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """Updates graph routing costs using an accelerated spatial index lookup."""

        # find the tiles needed to be pulled from tomtom
        self.last_parsed_segments = []
        needed_tiles = self.get_required_tiles_for_graph(graph)
        print(
            f"[*] Map Display v4 Sync: Requesting tiles: {needed_tiles} at Zoom Level {self.zoom}..."
        )
        if not needed_tiles:
            return graph

        # load the tiles required in WGS 84
        traffic_segments = self.fetch_all_tiles_concurrently(needed_tiles)
        print(
            f"[+] Successfully parsed {len(traffic_segments)} active geometric vector features."
        )
        if not traffic_segments:
            return graph

        # ---------- DEBUG EXPORT ----------
        os.makedirs("debug", exist_ok=True)
        gdf = gpd.GeoDataFrame(traffic_segments, geometry="geometry", crs="EPSG:4326")
        gdf.to_file("debug/tomtom_segments.geojson", driver="GeoJSON")
        print("[+] Exported debug/tomtom_segments.geojson")

        # processes the graph edges into 2 arrays.
        # first array stores the edges as their geometries in WKT/Shapely format
        # second stores the starting node (u), end node (v), key (k), data reference
        graph_edges = []
        edge_references = []
        for u, v, k, edge_data in graph.edges(keys=True, data=True):
            if "geometry" in edge_data:
                graph_edges.append(edge_data["geometry"])
                edge_references.append((u, v, k, edge_data))
        if not graph_edges:
            print("[-] Error: Graph edges are missing geometry elements.")
            return graph

        # constructs a sort tile recursive tree to store the edges while maintaining their spatial info
        # this reduces the graph lookup to O(M log N )
        spatial_tree = STRtree(graph_edges)

        # 0.0002 degrees is ~22 meters at the equator (safe fallback buffer for GPS offsets)
        matching_tolerance_degrees = 0.0002
        updated_count = 0

        for segment in traffic_segments:
            segment_geom = segment["geometry"]

            # Find any edges whose bounding envelopes overlap with our traffic line segment
            # creates a buffer around the segment (using flat caps 'cap_style=2' to prevent bleed)
            buffered_segment = segment_geom.buffer(
                matching_tolerance_degrees, cap_style=2
            )
            candidate_indices = spatial_tree.query(buffered_segment)

            # FIXED: Corrected indentation to live inside the segment loop
            for idx in candidate_indices:
                # Finds the best matching edges that correspond to target segment
                u, v, k, edge_data = edge_references[idx]
                edge_line = graph_edges[idx]

                # Verify that the traffic line closely shares a path with the road edge
                if edge_line.intersects(buffered_segment) or edge_line.distance(
                    segment_geom
                ) <= (matching_tolerance_degrees):
                    # FIXED: Pull traffic metrics from TomTom (segment) instead of empty graph fields
                    edge_data["traffic_level"] = segment["traffic_level"]

                    if segment.get("closed", False):
                        edge_data["closed"] = True
                        edge_data["routing_cost"] = float("inf")
                    else:
                        edge_data["closed"] = False
                        # Dynamically adjust your weight factor/routing_cost logic here if needed

                    # FIXED: Safely unpack 'name' from OSM to ensure it doesn't pass downstream lists
                    osm_name = edge_data.get("name", "Unknown")
                    if isinstance(osm_name, list):
                        osm_name = ", ".join(map(str, osm_name))

                    segment_data = {
                        "geometry": segment_geom,  # Must be a Shapely LineString
                        "traffic_level": segment[
                            "traffic_level"
                        ],  # Speed ratio (0.0 to 1.0)
                        "closed": edge_data["closed"],  # Boolean flag
                        "name": str(osm_name),  # Street name string
                    }
                    self.last_parsed_segments.append(segment_data)
                    updated_count += 1

        print(f"[+] Synced traffic variables across {updated_count} edge segments.")
        return graph
