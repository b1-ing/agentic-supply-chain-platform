# services/lta_service.py

import os
import time
from typing import List, Dict, Any, Tuple
import requests
import networkx as nx
from shapely.geometry import LineString
from shapely.strtree import STRtree
from dotenv import load_dotenv

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

    def fetch_all_pages(self, endpoint: str) -> List[Dict[str, Any]]:
        """Handles the 500-record pagination limit automatically via OData ?$skip"""
        results = []
        skip = 0
        url = f"{self.base_url}/{endpoint}"

        while True:
            params = {"$skip": skip} if skip > 0 else {}
            try:
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                if response.status_code != 200:
                    print(f"[-] LTA API Error {response.status_code} on {endpoint}: {response.text}")
                    break

                data = response.json()
                records = data.get("value", [])

                if not records:
                    break

                results.extend(records)

                if len(records) < 500:
                    break  # Fetched the last page

                skip += 500
                time.sleep(0.1)  # Small throttle to respect rate limits
            except Exception as e:
                print(f"[-] Request failed on endpoint {endpoint}: {e}")
                break

        return results


class LTATrafficService:
    def __init__(self, client: LTADataMallClient):
        self.client = client

        # Endpoint definitions
        self.speed_bands_endpoint = "TrafficSpeedBandsv2"
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
            8: 0.0   # > 80 km/h
        }

    # ==========================================
    # STREAM 1: SPATIAL SPEED BAND INJECTION
    # ==========================================
    def sync_speed_bands_to_graph(self, graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
        """Spatially projects paginated LTA speed segments onto OpenStreetMap graph edges."""
        lta_segments = self.client.fetch_all_pages(self.speed_bands_endpoint)
        print(f"[*] [Speed Bands] Ingested {len(lta_segments)} raw national road links.")

        if not lta_segments:
            return graph

        # 1. Index your NetworkX edge lines spatially
        graph_edges = []
        edge_references = []
        for u, v, k, edge_data in graph.edges(keys=True, data=True):
            if "geometry" in edge_data:
                graph_edges.append(edge_data["geometry"])
                edge_references.append((u, v, k, edge_data))
            else:
                node_u, node_v = graph.nodes[u], graph.nodes[v]
                fallback_line = LineString([(node_u["x"], node_u["y"]), (node_v["x"], node_v["y"])])
                graph_edges.append(fallback_line)
                edge_references.append((u, v, k, edge_data))

        spatial_tree = STRtree(graph_edges)

        # Buffer window set to ~45 meters to safely link parallel highway dividers
        match_buffer_degrees = 0.0004
        updated_count = 0

        # 2. Loop through spatial links and map them
        # Replace the loop in your sync_speed_bands_to_graph function with this:

        for item in lta_segments:
            try:
                summary = item.get("Location", "")
                coords = [float(c) for c in summary.replace(",", " ").split()]
                if len(coords) < 4:
                    continue

                # Explicitly map them out
                s_lat, s_lon, e_lat, e_lon = coords[0], coords[1], coords[2], coords[3]

                # Fix: Create a bounding box envelope using both points
                # to capture any OSM street segments running between or near them
                from shapely.geometry import MultiPoint
                lta_points = MultiPoint([(s_lon, s_lat), (e_lon, e_lat)])

                # Increase buffer slightly (~100 meters) to handle wide expressway dividers
                buffered_envelope = lta_points.envelope.buffer(0.0009)

                # Query index for candidate matches inside this regional box
                candidate_indices = spatial_tree.query(buffered_envelope)

                band_value = int(item.get("SpeedBand", 5))
                traffic_ratio = self.band_to_traffic_multiplier.get(band_value, 0.0)

                for idx in candidate_indices:
                    u, v, k, edge_data = edge_references[idx]
                    edge_line = graph_edges[idx]

                    # If the OSM road edge sits inside our LTA corridor envelope, patch it
                    if edge_line.intersects(buffered_envelope):
                        edge_data["traffic_level"] = traffic_ratio
                        edge_data["lta_link_id"] = item.get("LinkID")
                        edge_data["speed_band"] = band_value

                        base_time = edge_data.get("travel_time", 1.0)
                        edge_data["routing_cost"] = base_time * (1.0 + traffic_ratio)
                        updated_count += 1

            except (KeyError, ValueError, IndexError):
                continue

        print(f"[+] [Speed Bands] Sync complete. Injected parameters across {updated_count} spatial edge lines.")
        return graph

    # ==========================================
    # STREAM 2: TEXTUAL TRAVEL TIME EXTRACTION
    # ==========================================
    def fetch_macro_travel_times(self, node_registry: Dict[str, int]) -> Dict[Tuple[int, int], int]:
        """
        Fetches checkpoint-to-checkpoint times and maps them to clean matrix index edge-costs.
        Returns: {(from_node_id, to_node_id): duration_in_seconds}
        """
        raw_travel_times = self.client.fetch_all_pages(self.travel_times_endpoint)
        print(f"[*] [Travel Times] Ingested {len(raw_travel_times)} macro corridor segments.")

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