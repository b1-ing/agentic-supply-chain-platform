# services/traffic/graph.py

from copy import deepcopy
from pathlib import Path
from models.world.world_state import WorldState
from models.traffic.traffic_incident import TrafficIncident
from models.traffic.road_speed_band import RoadSpeedBand
import json

class TrafficGraphService:
    """
    Applies live traffic information onto the routing graph.

    Responsibilities
    ----------------
    - Reset graph edge weights
    - Apply speed band penalties
    - Apply incident penalties
    - Apply road closure
    """

    def __init__(
            self,
            speed_band_mapping_path: str | Path = (
                "cache/speed_band_mapping.json"
            ),
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

        self.speed_band_mapping_path = Path(
            speed_band_mapping_path
        )

        self.speed_band_mapping = (
            self._load_speed_band_mapping()
        )

    def update(
            self,
            world: WorldState,
            speed_bands: list[RoadSpeedBand],
            incidents: list[TrafficIncident],
    ):
        graph = world.graph

        self._reset(graph)

        self._apply_speed_bands(
            graph,
            speed_bands,
        )

        self._apply_incidents(
            graph,
            incidents,
        )

        return graph

    ################################################################
    # SpeedBand cache
    ################################################################

    def _load_speed_band_mapping(self):

        if not self.speed_band_mapping_path.exists():

            raise FileNotFoundError(
                "SpeedBand mapping cache not found: "
                f"{self.speed_band_mapping_path}"
            )

        print(
            "[*] Loading SpeedBand → OSM cache..."
        )

        with open(
                self.speed_band_mapping_path,
                "r",
                encoding="utf-8",
        ) as f:

            mapping = json.load(f)

        print(
            f"[+] Loaded {len(mapping):,} "
            "SpeedBand mappings."
        )

        return mapping


    ####################################################################
    # Reset
    ####################################################################

    def _reset(self, graph):

        for _, _, _, data in graph.edges(keys=True, data=True):

            if "base_travel_time" in data:
                data["travel_time"] = data["base_travel_time"]

    ####################################################################
    # Speed Bands
    ####################################################################
    def _apply_speed_bands(
            self,
            graph,
            speed_bands,
    ):

        matched = 0
        missing = 0


        for band in speed_bands:

            ############################################################
            # Look up precomputed LTA -> OSM mapping
            ############################################################
            entry = self.speed_band_mapping.get(
                band.incident.metadata["LinkID"]
            )

            if not entry:
                missing += 1
                continue
            matched += 1

            edges = entry["edges"]

            ############################################################
            # Determine traffic multiplier
            ############################################################

            multiplier = {
                1: 3.0,
                2: 2.2,
                3: 1.5,
                4: 1.2,
                5: 1.0,
            }.get(
                band.incident.speed_band,
                1.0,
            )

            ############################################################
            # Apply to every mapped OSM edge
            ############################################################

            for u, v, k in edges:

                data = graph[u][v][k]

                print(data)

                #
                # Always calculate from free-flow travel time.
                #

                base = data["travel_time"]

                traffic_penalty = data.get(
                    "traffic_penalty",
                    0,
                )

                data["adjusted_travel_time"] = (
                    base * multiplier
                    + traffic_penalty
                )


            print(
                f"[SpeedBands] matched={matched}, "
                f"missing={missing}, "
                f"total={matched + missing}"
            )
    ####################################################################
    # Incidents
    ####################################################################

    def _apply_incidents(
            self,
            graph,
            incidents,
    ):

        for incident in incidents:

            if incident.edge is None:
                continue

            u, v, k = incident.edge

            data = graph[u][v][k]

            data["travel_time"] *= 5