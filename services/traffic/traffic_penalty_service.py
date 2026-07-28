# services/traffic/traffic_penalty_service.py

from collections import defaultdict
import networkx as nx

from services.traffic.penalty_policy import PenaltyPolicy


class TrafficPenaltyService:
    """
    Applies traffic penalties onto the road graph.

    Responsibilities
    ----------------
    - Reset edges back to their base travel time.
    - Combine overlapping penalties.
    - Clamp penalties.
    - Update travel_time.

    NOT responsible for
    -------------------
    - Fetching incidents
    - Matching incidents to edges
    - LLM reasoning
    """

    def __init__(self):

        self.policy = PenaltyPolicy()

    ####################################################################
    # Public
    ####################################################################

    def apply(
        self,
        graph: nx.MultiDiGraph,
        matched_incidents: list,
    ) -> nx.MultiDiGraph:

        #
        # 1. Reset graph
        #

        self._reset_graph(graph)

        #
        # 2. Group penalties by edge
        #

        penalties = defaultdict(list)

        for incident in matched_incidents:
            for edge in incident.affected_edges:
                penalties[edge].append(self.policy.penalty_seconds(incident))

        #
        # 3. Apply combined penalties
        #

        for edge, values in penalties.items():
            u, v, key = edge

            data = graph[u][v][key]

            base = data["base_travel_time"]

            penalty = self._combine(values)

            data["traffic_penalty"] = penalty

            data["travel_time"] = base + penalty

        return graph

    ####################################################################
    # Internal
    ####################################################################

    def _reset_graph(
        self,
        graph,
    ):
        """
        Remove all previous penalties.
        """

        for _, _, _, data in graph.edges(
            keys=True,
            data=True,
        ):
            if "base_travel_time" not in data:
                data["base_travel_time"] = data["travel_time"]

            data["traffic_penalty"] = 0

            data["travel_time"] = data["base_travel_time"]

    ####################################################################

    def _combine(
        self,
        penalties: list[float],
    ) -> float:
        """
        Combine overlapping penalties.

        Example

        congestion = 300

        accident = 250

        total = 300 + 0.5 * 250 = 425

        rather than

        550
        """

        if len(penalties) == 0:
            return 0

        penalties = sorted(
            penalties,
            reverse=True,
        )

        total = penalties[0]

        for p in penalties[1:]:
            total += p * 0.5

        return min(
            total,
            self.policy.max_penalty_seconds,
        )
