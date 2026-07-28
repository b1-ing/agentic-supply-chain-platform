from difflib import get_close_matches

import networkx as nx
import osmnx as ox

from models.matched_traffic_incident import MatchedTrafficIncident, MatchType
from models.traffic_incident import TrafficIncident


class TrafficIncidentMatcher:
    """
    Matches real-world traffic incidents onto the road graph.

    Responsibilities
    ----------------
    - Determine which graph edges are affected.
    - Return a MatchedTrafficIncident.
    - DO NOT modify the graph.
    - DO NOT apply penalties.
    """

    def match(
        self,
        graph: nx.MultiDiGraph,
        incident: TrafficIncident,
    ) -> MatchedTrafficIncident:

        #
        # 1. Coordinates available
        #

        if incident.latitude is not None and incident.longitude is not None:
            return self._match_by_coordinates(
                graph,
                incident,
            )

        #
        # 2. Road name available
        #

        if incident.road_name:
            #
            # Slip roads / exits
            #

            if (
                "slip" in incident.description.lower()
                or "exit" in incident.description.lower()
            ):
                return self._match_slip_road(
                    graph,
                    incident,
                )

            return self._match_by_road_name(
                graph,
                incident,
            )

        #
        # 3. Fallback
        #

        return MatchedTrafficIncident(
            incident=incident,
            match_type=MatchType.UNKNOWN,
            confidence=0.0,
        )

    ####################################################################
    # Coordinate matching
    ####################################################################

    def _match_by_coordinates(
        self,
        graph,
        incident,
    ):

        u, v, key = ox.distance.nearest_edges(
            graph,
            incident.longitude,
            incident.latitude,
        )

        return MatchedTrafficIncident(
            incident=incident,
            affected_edges=[(u, v, key)],
            match_type=MatchType.COORDINATE,
            confidence=1.0,
        )

    ####################################################################
    # Road-name matching
    ####################################################################

    def _match_by_road_name(
        self,
        graph,
        incident,
    ):

        affected = []

        target = incident.road_name.lower()

        #
        # Exact matches
        #

        for u, v, key, data in graph.edges(keys=True, data=True):
            name = data.get("name")

            if name is None:
                continue

            #
            # OSM road names can be lists
            #

            if isinstance(name, list):
                names = [n.lower() for n in name]

            else:
                names = [str(name).lower()]

            if target in names:
                affected.append((u, v, key))

        #
        # Fuzzy matching
        #

        if not affected:
            all_names = set()

            for _, _, _, data in graph.edges(keys=True, data=True):
                name = data.get("name")

                if name is None:
                    continue

                if isinstance(name, list):
                    all_names.update(name)

                else:
                    all_names.add(name)

            match = get_close_matches(
                incident.road_name,
                list(all_names),
                n=1,
                cutoff=0.8,
            )

            if match:
                matched_name = match[0].lower()

                for u, v, key, data in graph.edges(keys=True, data=True):
                    name = data.get("name")

                    if name is None:
                        continue

                    if isinstance(name, list):
                        names = [n.lower() for n in name]

                    else:
                        names = [str(name).lower()]

                    if matched_name in names:
                        affected.append((u, v, key))

                confidence = 0.8

            else:
                confidence = 0.0

        else:
            confidence = 0.95

        return MatchedTrafficIncident(
            incident=incident,
            affected_edges=affected,
            match_type=MatchType.ROAD_NAME,
            confidence=confidence,
            matched_road=incident.road_name,
        )

    ####################################################################
    # Slip-road matching
    ####################################################################

    def _match_slip_road(
        self,
        graph,
        incident,
    ):
        """
        Placeholder implementation.

        Future improvements:
        - Parse "PIE Exit 12".
        - Match ramp edges.
        - Use cached LTA ↔ OSM mapping.
        """

        #
        # For now fall back to road-name matching.
        #

        result = self._match_by_road_name(
            graph,
            incident,
        )

        result.match_type = MatchType.SLIP_ROAD

        result.confidence *= 0.9

        return result

    ####################################################################
    # Radius search
    ####################################################################

    def radius_search(
        self,
        graph,
        latitude,
        longitude,
        radius_m,
    ):
        """
        Returns all edges within a radius.

        Used later by TrafficPenaltyService for
        accidents, floods, large events, etc.
        """

        centre = ox.distance.nearest_nodes(
            graph,
            longitude,
            latitude,
        )

        lengths = nx.single_source_dijkstra_path_length(
            graph,
            centre,
            cutoff=radius_m,
            weight="length",
        )

        affected = []

        for u, v, key in graph.edges(keys=True):
            if u in lengths or v in lengths:
                affected.append((u, v, key))

        return affected
