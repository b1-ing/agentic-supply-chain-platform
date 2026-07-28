# services/order/graph_snap_service.py

import osmnx as ox
import networkx as nx


class GraphSnapService:
    """
    Snaps latitude/longitude coordinates onto the road network.

    Responsibilities
    ----------------
    - Find the nearest drivable OSM node.
    - Return the graph node ID.

    Not responsible for:
    - Geocoding addresses
    - Routing
    - Order processing
    """

    def snap(
        self,
        graph: nx.MultiDiGraph,
        lat: float,
        lon: float,
    ) -> int:
        """
        Snap a coordinate to the nearest road node.

        Parameters
        ----------
        graph
            Road network.

        lat
            Latitude.

        lon
            Longitude.

        Returns
        -------
        int
            Nearest graph node ID.
        """

        if graph is None:
            raise ValueError("Graph cannot be None.")

        if lat is None or lon is None:
            raise ValueError("Latitude and longitude must both be provided.")

        node = ox.distance.nearest_nodes(
            graph,
            X=lon,  # OSMnx expects longitude first
            Y=lat,
        )

        return int(node)

    def snap_many(
        self,
        graph: nx.MultiDiGraph,
        coordinates: list[tuple[float, float]],
    ) -> list[int]:
        """
        Snap multiple coordinates.

        Parameters
        ----------
        graph
            Road network.

        coordinates
            List of (latitude, longitude) tuples.

        Returns
        -------
        list[int]
            Graph node IDs.
        """

        return [self.snap(graph, lat, lon) for lat, lon in coordinates]
