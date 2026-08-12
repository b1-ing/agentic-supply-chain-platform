from typing import Sequence

import networkx as nx
import osmnx as ox


class ValhallaService:
    """
    Provides shortest-path operations on the road network.

    Responsibilities
    ----------------
    - Shortest paths
    - Travel times
    - Route geometry

    Not responsible for
    -------------------
    - Vehicle routing
    - ORTools
    - Orders
    - Fleet optimisation
    """

    def nearest_node(
        self,
        graph: nx.MultiDiGraph,
        lat: float,
        lon: float,
    ) -> int:

        return ox.distance.nearest_nodes(
            graph,
            lon,
            lat,
        )

    def shortest_path(
        self,
        graph: nx.MultiDiGraph,
        source: int,
        target: int,
    ) -> list[int]:

        return nx.shortest_path(
            graph,
            source,
            target,
            weight="travel_time",
        )

    def travel_time(
        self,
        graph: nx.MultiDiGraph,
        source: int,
        target: int,
    ) -> float:

        return nx.shortest_path_length(
            graph,
            source,
            target,
            weight="travel_time",
        )

    def travel_distance(
        self,
        graph,
        source,
        target,
    ) -> float:

        path = self.shortest_path(
            graph,
            source,
            target,
        )

        distance = 0

        for u, v in zip(path[:-1], path[1:]):
            edge = min(
                graph[u][v].values(),
                key=lambda e: e["length"],
            )

            distance += edge["length"]

        return distance

    def route_geometry(
        self,
        graph,
        source,
        target,
    ) -> Sequence[int]:

        return self.shortest_path(
            graph,
            source,
            target,
        )
