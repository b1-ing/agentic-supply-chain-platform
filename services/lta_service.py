# services/lta_service.py

import os
import time
from typing import List, Dict, Any, Tuple
import requests
import networkx as nx
from shapely.geometry import LineString
from shapely.strtree import STRtree
from dotenv import load_dotenv
import httpx
import asyncio
import math
import geopandas as gpd
import json

load_dotenv()


class LTADataMallClient:
    def __init__(self, account_key: str = None):
        self.account_key = account_key or os.getenv("LTA_ACCOUNT_KEY")
        if not self.account_key:
            raise ValueError(
                "LTA AccountKey must be provided or set in environment variables."
            )

        self.base_url = "https://datamall2.mytransport.sg/ltaodataservice"
        self.headers = {"AccountKey": self.account_key, "accept": "application/json"}

    def export_lta_segments(self, lta_segments, output="debug/lta_segments.geojson"):
        rows = []

        for seg in lta_segments:
            try:
                line = LineString(
                    [
                        (float(seg["StartLon"]), float(seg["StartLat"])),
                        (float(seg["EndLon"]), float(seg["EndLat"])),
                    ]
                )

                rows.append(
                    {
                        "link_id": seg["LinkID"],
                        "road_name": seg["RoadName"],
                        "road_category": int(seg["RoadCategory"]),
                        "speed_band": int(seg["SpeedBand"]),
                        "min_speed": int(seg["MinimumSpeed"]),
                        "max_speed": int(seg["MaximumSpeed"]),
                        "geometry": line,
                    }
                )

            except Exception as e:
                print(f"Skipping LinkID {seg.get('LinkID')}: {e}")

        gdf = gpd.GeoDataFrame(
            rows,
            geometry="geometry",
            crs="EPSG:4326",
        )

        os.makedirs("debug", exist_ok=True)

        gdf.to_file(output, driver="GeoJSON")

        print(f"[+] Exported {len(gdf)} LTA segments to {output}")

    async def fetch_all_pages_async(self, endpoint: str) -> List[Dict[str, Any]]:
        """Handles the 500-record pagination limit asynchronously via OData ?$skip with a 2s throttle."""
        results = []
        skip = 0
        url = f"{self.base_url}/{endpoint}"

        # Use an async client context manager (or pass a shared client instance to the method)
        async with httpx.AsyncClient() as client:
            while True:
                params = {"$skip": skip} if skip > 0 else {}
                try:
                    response = await client.get(
                        url, headers=self.headers, params=params, timeout=15.0
                    )

                    if response.status_code != 200:
                        print(
                            f"[-] LTA API Error {response.status_code} on {endpoint}: {response.text}"
                        )
                        break

                    data = response.json()
                    records = data.get("value", [])

                    if not records:
                        break

                    results.extend(records)

                    if len(records) < 500:
                        break  # Fetched the last page

                    skip += 500

                    # Non-blocking async sleep for 2 seconds
                    await asyncio.sleep(0.2)

                except Exception as e:
                    print(f"[-] Request failed on endpoint {endpoint}: {e}")
                    break

        self.export_lta_segments(results)
        return results

    def fetch_all_pages(self, endpoint: str) -> List[Dict[str, Any]]:
        """Handles the 500-record pagination limit automatically via OData ?$skip"""
        results = []
        skip = 0
        url = f"{self.base_url}/{endpoint}"

        while skip < 500:  # REVERT TO TRUE AFTER TESTING
            params = {"$skip": skip} if skip > 0 else {}
            try:
                response = requests.get(
                    url, headers=self.headers, params=params, timeout=15
                )
                if response.status_code != 200:
                    print(
                        f"[-] LTA API Error {response.status_code} on {endpoint}: {response.text}"
                    )
                    break

                data = response.json()
                records = data.get("value", [])

                if not records:
                    break

                results.extend(records)

                if len(records) < 500:
                    break  # Fetched the last page

                skip += 500
                time.sleep(1)  # Small throttle to respect rate limits
            except Exception as e:
                print(f"[-] Request failed on endpoint {endpoint}: {e}")
                break

        return results


class LTATrafficService:
    def __init__(self, client: LTADataMallClient):
        self.client = client

        # Endpoint definitions
        self.speed_bands_endpoint = "v4/TrafficSpeedBands"
        self.travel_times_endpoint = "EstTravelTimes"

        # Maps LTA Speed Bands to relative routing time penalties
        self.band_to_traffic_multiplier = {
            1: 1.0,  # < 20 km/h (Extreme Congestion -> heavy travel penalty)
            2: 0.7,  # 20-30 km/h
            3: 0.4,  # 30-40 km/h
            4: 0.2,  # 40-50 km/h
            5: 0.0,  # 50-60 km/h (Normal Flow)
            6: 0.0,  # 60-70 km/h (Free Flow)
            7: 0.0,  # 70-80 km/h
            8: 0.0,  # > 80 km/h
        }

    def calculate_bearing(self, lat1, lon1, lat2, lon2):
        """Calculates the bearing between two points in degrees (0-360)."""
        d_lon = math.radians(lon2 - lon1)
        y = math.sin(d_lon) * math.cos(math.radians(lat2))
        x = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - math.sin(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.cos(d_lon)
        return (math.degrees(math.atan2(y, x)) + 360) % 360

    def is_same_direction(self, bearing1, bearing2, tolerance=35):
        """Checks if two bearings point in roughly the same direction."""
        diff = abs(bearing1 - bearing2)
        return min(diff, 360 - diff) <= tolerance

    # ==========================================
    # STREAM 1: SPATIAL SPEED BAND INJECTION
    # ==========================================
    async def sync_network_flow_async(
        self, graph: nx.MultiDiGraph, cache_path: str = "cache/lta_osm_mapping.json"
    ) -> nx.MultiDiGraph:
        """Spatially projects paginated LTA speed segments onto OpenStreetMap graph edges,
        caching the spatial mapping to disk to bypass heavy calculations on subsequent runs."""

        lta_segments = await self.client.fetch_all_pages_async(
            self.speed_bands_endpoint
        )
        print(
            f"[*] [Speed Bands] Ingested {len(lta_segments)} raw national road links."
        )

        if not lta_segments:
            return graph

        mapping_cache = {}
        cache_exists = os.path.exists(cache_path)

        if cache_exists:
            print(
                f"[*] [Cache] Found spatial mapping cache at {cache_path}. Loading..."
            )
            try:
                with open(cache_path, "r") as f:
                    # JSON keys are always strings, so we convert edge keys back to proper types later
                    mapping_cache = json.load(f)
            except Exception as e:
                print(f"[!] Failed to read cache: {e}. Recomputing spatial tree...")
                cache_exists = False

        # --- Phase 1: Build or Load Spatial Mapping ---
        if not cache_exists:
            print(
                "[*] [Spatial Tree] No valid cache found. Indexing OSM network spatially..."
            )
            graph_edges = []
            edge_references = []

            for u, v, k, edge_data in graph.edges(keys=True, data=True):
                if "geometry" in edge_data:
                    graph_edges.append(edge_data["geometry"])
                else:
                    node_u, node_v = graph.nodes[u], graph.nodes[v]
                    fallback_line = LineString(
                        [(node_u["x"], node_u["y"]), (node_v["x"], node_v["y"])]
                    )
                    graph_edges.append(fallback_line)
                edge_references.append((u, v, k))

            spatial_tree = STRtree(graph_edges)

            print(
                "[*] [Spatial Tree] Computing LTA-to-OSM intersections (this may take a moment)..."
            )
            for item in lta_segments:
                link_id = item.get("LinkID")
                if not link_id:
                    continue

                try:
                    s_lat = float(item.get("StartLat", 0))
                    s_lon = float(item.get("StartLon", 0))
                    e_lat = float(item.get("EndLat", 0))
                    e_lon = float(item.get("EndLon", 0))

                    lta_line = LineString([(s_lon, s_lat), (e_lon, e_lat)])
                    lta_bearing = self.calculate_bearing(s_lat, s_lon, e_lat, e_lon)
                    tight_line_buffer = lta_line.buffer(0.00023)  # ~25 meters

                    candidate_indices = spatial_tree.query(tight_line_buffer)
                    matched_edges = []

                    for idx in candidate_indices:
                        u, v, k = edge_references[idx]
                        edge_line = graph_edges[idx]

                        if edge_line.intersects(tight_line_buffer):
                            edge_coords = list(edge_line.coords)
                            if len(edge_coords) >= 2:
                                osm_s_lon, osm_s_lat = edge_coords[0]
                                osm_e_lon, osm_e_lat = edge_coords[-1]
                                osm_bearing = self.calculate_bearing(
                                    osm_s_lat, osm_s_lon, osm_e_lat, osm_e_lon
                                )

                                if not self.is_same_direction(
                                    lta_bearing, osm_bearing, tolerance=40
                                ):
                                    chunk_debug = False  # skip wrong highway direction
                                    continue

                            # Store matching edge references as primitive types for JSON compatibility
                            matched_edges.append([u, v, k])

                    if matched_edges:
                        mapping_cache[link_id] = matched_edges

                except (KeyError, ValueError, IndexError):
                    continue

            # Save computed mapping to disk
            os.makedirs(os.path.dirname(cache_path), exist_ok=True)
            with open(cache_path, "w") as f:
                json.dump(mapping_cache, f, indent=4)
            print(
                f"[+] [Cache] Spatial mapping successfully saved to disk at {cache_path}"
            )

        # --- Phase 2: Apply Live Traffic Speed Data ---
        updated_count = 0
        for item in lta_segments:
            link_id = item.get("LinkID")
            if not link_id or link_id not in mapping_cache:
                continue

            band_value = int(item.get("SpeedBand", 5))
            traffic_ratio = self.band_to_traffic_multiplier.get(band_value, 0.0)

            # Retrieve matched edges from cache and apply attributes
            for u, v, k in mapping_cache[link_id]:
                # Guard check in case the underlying graph changed since caching
                if graph.has_edge(u, v, k):
                    edge_data = graph[u][v][k]
                    edge_data["traffic_level"] = traffic_ratio
                    edge_data["lta_link_id"] = link_id
                    edge_data["speed_band"] = band_value

                    base_time = edge_data.get("travel_time", 1.0)
                    edge_data["routing_cost"] = base_time * (1.0 + traffic_ratio)
                    updated_count += 1

        print(
            f"[+] [Speed Bands] Sync complete. Injected parameters across {updated_count} network edges."
        )
        return graph

    # ==========================================
    # STREAM 2: TEXTUAL TRAVEL TIME EXTRACTION
    # ==========================================
    def fetch_macro_travel_times(
        self, node_registry: Dict[str, int]
    ) -> Dict[Tuple[int, int], int]:
        """
        Fetches checkpoint-to-checkpoint times and maps them to clean matrix index edge-costs.
        Returns: {(from_node_id, to_node_id): duration_in_seconds}
        """
        raw_travel_times = self.client.fetch_all_pages(self.travel_times_endpoint)
        print(
            f"[*] [Travel Times] Ingested {len(raw_travel_times)} macro corridor segments."
        )

        macro_edge_costs = {}
        for segment in raw_travel_times:
            start_point = segment.get("StartPoint")
            end_point = segment.get("EndPoint")
            est_time_mins = segment.get("EstTime", 0)

            if start_point in node_registry and end_point in node_registry:
                from_id = node_registry[start_point]
                to_id = node_registry[end_point]

                # Convert minutes to seconds for internal solver precision
                macro_edge_costs[(from_id, to_id)] = int(est_time_mins * 60)

        return macro_edge_costs
