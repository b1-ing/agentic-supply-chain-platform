import networkx as nx

from services.traffic.traffic_penalty_service import TrafficPenaltyService


class GraphUpdateService:
    """
    Applies analysed traffic incidents onto the road graph.

    Pipeline

        MatchedTrafficIncident
                    ↓
        TrafficPenaltyService
                    ↓
            Updated graph

    This service owns no state.
    """

    def __init__(self):

        self.penalty_service = TrafficPenaltyService()

    ####################################################################
    # Public
    ####################################################################

    def update(
            self,
            graph: nx.MultiDiGraph,
            matched_incidents: list,
    ) -> nx.MultiDiGraph:
        """
        Returns an updated graph with all penalties applied.

        Previous penalties are cleared automatically before
        applying the new traffic snapshot.
        """

        if graph is None:
            raise ValueError("Graph cannot be None.")

        updated_graph = self.penalty_service.apply(
            graph,
            matched_incidents,
        )

        return updated_graph
