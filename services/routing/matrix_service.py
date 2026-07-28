# services/matrix_service.py

import networkx as nx
import numpy as np

from models.order.routing_location import RoutingLocation
from models.routing.travel_matrix import TravelMatrix


class MatrixService:
    def build(
        self,
        world,
        locations: list[RoutingLocation],
    ) -> TravelMatrix:
        """
        Compute an NxN travel-time matrix over the supplied routing locations.
        """

        n = len(locations)

        matrix = np.full((n, n), np.inf)

        for i, source in enumerate(locations):
            lengths = nx.single_source_dijkstra_path_length(
                world.graph,
                source.graph_node,
                weight="travel_time",
            )

            matrix[i, i] = 0

            for j, target in enumerate(locations):
                matrix[i, j] = lengths.get(
                    target.graph_node,
                    np.inf,
                )

        return TravelMatrix(
            matrix=matrix,
            locations=locations,
        )
