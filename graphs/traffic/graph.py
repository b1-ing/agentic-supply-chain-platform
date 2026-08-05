# services/traffic/graph.py

from copy import deepcopy

from models.world.world_state import WorldState
from models.traffic.traffic_incident import TrafficIncident
from models.traffic.road_speed_band import RoadSpeedBand


class TrafficGraphService:
    """
    Applies live traffic information onto the routing graph.

    Responsibilities
    ----------------
    - Reset graph edge weights
    - Apply speed band penalties
    - Apply incident penalties
    - Apply road closures
    """

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

    for band in speed_bands:

        edges = self.speed_band_mapping.get_edges(
            band.link_id,
        )

        if not edges:
            continue

        multiplier = {
            1: 3.0,
            2: 2.2,
            3: 1.5,
            4: 1.2,
            5: 1.0,
        }.get(
            band.speed_band,
            1.0,
        )

        for u, v, k in edges:

            data = graph[u][v][k]

            #
            # Always use the free-flow travel time.
            #

            base = data["base_travel_time"]

            traffic_penalty = data.get(
                "traffic_penalty",
                0,
            )

            data["travel_time"] = (
                    base * multiplier
                    + traffic_penalty
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