# services/traffic/road_matcher.py

import json
from pathlib import Path

import networkx as nx
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree

from models.traffic.matched_traffic_incident import (
    MatchedTrafficIncident,
    MatchType,
)


class RoadMatcher:
    def __init__(
        self,
        speed_band_mapping_path: str | Path = ("cache/speed_band_mapping.json"),
    ):

        ############################################################
        # Incident spatial index
        ############################################################

        self.tree = None
        self.edges = []
        self.graph = None

        ############################################################
        # LTA SpeedBand cache
        ############################################################

        self.speed_band_mapping_path = Path(speed_band_mapping_path)

        self.speed_band_mapping = self._load_speed_band_mapping()

    ################################################################
    # SpeedBand cache
    ################################################################

    def _load_speed_band_mapping(self):

        if not self.speed_band_mapping_path.exists():
            raise FileNotFoundError(
                f"SpeedBand mapping cache not found: {self.speed_band_mapping_path}"
            )

        print("[*] Loading SpeedBand → OSM cache...")

        with open(
            self.speed_band_mapping_path,
            "r",
            encoding="utf-8",
        ) as f:
            mapping = json.load(f)

        print(f"[+] Loaded {len(mapping):,} SpeedBand mappings.")

        return mapping

    ################################################################
    # Build spatial index
    ################################################################
    #
    # Used for traffic incidents.
    #
    # SpeedBands DO NOT use this index.
    #
    ################################################################

    def build_index(
        self,
        graph: nx.MultiDiGraph,
    ):

        self.graph = graph

        self.edges = []
        geometries = []

        for u, v, key, data in graph.edges(
            keys=True,
            data=True,
        ):
            geometry = data.get("geometry")

            #
            # Some OSM edges may not have
            # explicit geometry.
            #

            if geometry is None:
                u_data = graph.nodes[u]
                v_data = graph.nodes[v]

                geometry = LineString(
                    [
                        (
                            u_data["x"],
                            u_data["y"],
                        ),
                        (
                            v_data["x"],
                            v_data["y"],
                        ),
                    ]
                )

            geometries.append(geometry)

            self.edges.append(
                (
                    u,
                    v,
                    key,
                )
            )

        self.tree = STRtree(geometries)

        print(f"[+] Built incident spatial index for {len(self.edges):,} OSM edges.")

    ################################################################
    # Nearest edge
    ################################################################

    def nearest_edge(
        self,
        graph,
        latitude,
        longitude,
    ):

        #
        # Build the spatial index once.
        #

        if self.tree is None or self.graph is not graph:
            self.build_index(graph)

        point = Point(
            longitude,
            latitude,
        )

        geometry_index = self.tree.nearest(point)

        if geometry_index is None:
            return None

        return self.edges[int(geometry_index)]

    ################################################################
    # Match incidents
    ################################################################

    def match_incidents(
        self,
        graph: nx.MultiDiGraph,
        incidents,
    ):

        matched = []

        for incident in incidents:
            ########################################################
            # Coordinate-based incident
            ########################################################

            if incident.latitude is not None and incident.longitude is not None:
                edge = self.nearest_edge(
                    graph,
                    incident.latitude,
                    incident.longitude,
                )

                if edge is None:
                    continue

                matched.append(
                    MatchedTrafficIncident(
                        incident=incident,
                        affected_edges=[edge],
                        match_type=MatchType.COORDINATE,
                        confidence=1.0,
                    )
                )

                continue

            ########################################################
            # Road-name incident
            ########################################################

            if incident.road_name:
                edges = self._match_by_road_name(
                    graph,
                    incident.road_name,
                )

                matched.append(
                    MatchedTrafficIncident(
                        incident=incident,
                        affected_edges=edges,
                        match_type=MatchType.ROAD_NAME,
                        confidence=0.95 if edges else 0.0,
                        matched_road=incident.road_name,
                    )
                )

                continue

            ########################################################
            # Unknown incident
            ########################################################

            matched.append(
                MatchedTrafficIncident(
                    incident=incident,
                    affected_edges=[],
                    match_type=MatchType.UNKNOWN,
                    confidence=0.0,
                )
            )

        return matched

    ################################################################
    # Match SpeedBands
    ################################################################
    #
    # IMPORTANT:
    #
    # This does NOT perform spatial matching.
    #
    # It simply:
    #
    #     LTA link_id
    #          ↓
    #     JSON cache
    #          ↓
    #     OSM edges
    #
    ################################################################

    def match_speed_bands(
        self,
        graph: nx.MultiDiGraph,
        speed_bands,
    ):

        matched = []

        for band in speed_bands:
            link_id = str(band.link_id)

            cached = self.speed_band_mapping.get(link_id)

            ########################################################
            # No mapping
            ########################################################

            if cached is None:
                print(f"[MISS] No cached mapping for LTA SpeedBand {link_id}")

                continue

            ########################################################
            # Validate cached edges
            ########################################################

            affected_edges = []

            for edge in cached.get(
                "edges",
                [],
            ):
                #
                # JSON stores tuples as lists.
                #

                u, v, key = edge

                if not graph.has_edge(
                    u,
                    v,
                    key,
                ):
                    print(f"[MISS] Cached edge {edge} does not exist for LTA {link_id}")

                    continue

                affected_edges.append(
                    (
                        u,
                        v,
                        key,
                    )
                )

            ########################################################
            # No valid edges
            ########################################################

            if not affected_edges:
                print(f"[MISS] LTA {link_id} has no valid OSM edges")

                continue

            ########################################################
            # Create matched object
            ########################################################

            matched.append(
                MatchedTrafficIncident(
                    incident=band,
                    affected_edges=affected_edges,
                    match_type=MatchType.SPEED_BAND,
                    confidence=1.0,
                )
            )

        return matched

    ################################################################
    # Road-name matching
    ################################################################

    def _match_by_road_name(
        self,
        graph,
        road_name,
    ):

        affected = []

        target = road_name.lower()

        for u, v, key, data in graph.edges(
            keys=True,
            data=True,
        ):
            name = data.get("name")

            if name is None:
                continue

            if isinstance(
                name,
                list,
            ):
                names = [str(n).lower() for n in name]

            else:
                names = [str(name).lower()]

            if target in names:
                affected.append(
                    (
                        u,
                        v,
                        key,
                    )
                )

        return affected
