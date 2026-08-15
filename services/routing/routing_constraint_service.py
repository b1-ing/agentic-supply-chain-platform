from __future__ import annotations

import re
import networkx as nx

from datetime import datetime

from models.traffic.traffic_incident import TrafficIncident


class RoutingConstraintService:
    """
    Builds a routing graph with currently active operational
    restrictions applied.

    The original WorldState graph is never modified.

    Sources of restrictions:
        - Order-level avoid_road constraints
        - Active TrafficIncident road restrictions
    """

    def build_graph(
        self,
        world,
        avoid_roads: list[str] | None = None,
        now: datetime | None = None,
    ):
        """
        Return a restricted copy of the WorldState routing graph.

        Args:
            world:
                Current WorldState.

            avoid_roads:
                Explicit roads that the route must avoid.

            now:
                Time used to determine whether traffic incidents
                are currently active.

        Returns:
            A NetworkX graph with restricted edges removed.
        """

        avoid_roads = avoid_roads or []

        if now is None:
            now = datetime.now()

        graph = world.graph.copy()

        # ---------------------------------------------------------
        # Collect all road restrictions
        # ---------------------------------------------------------

        restricted_roads = set()

        # Explicit order constraints
        for road in avoid_roads:
            if road and road.strip():
                restricted_roads.add(
                    road.strip()
                )

        # Active traffic incidents
        for incident in world.traffic_events:

            if not self._is_active(
                incident,
                now,
            ):
                continue

            if not incident.road_name:
                continue

            if self._blocks_routing(
                incident
            ):
                restricted_roads.add(
                    incident.road_name
                )

        # ---------------------------------------------------------
        # Remove matching graph edges
        # ---------------------------------------------------------

        removed_edges = []

        patterns = [
            re.compile(
                r"\b"
                + re.escape(road.lower())
                + r"\b"
            )
            for road in restricted_roads
        ]

        for u, v, key, data in list(
            graph.edges(
                keys=True,
                data=True,
            )
        ):

            identifiers = self._edge_identifiers(
                data
            )

            should_remove = any(
                pattern.search(identifier)
                for pattern in patterns
                for identifier in identifiers
            )

            if not should_remove:
                continue

            graph.remove_edge(
                u,
                v,
                key,
            )

            removed_edges.append(
                {
                    "u": u,
                    "v": v,
                    "key": key,
                    "road": identifiers,
                }
            )

        return graph, removed_edges

    # =============================================================
    # Incident handling
    # =============================================================

    @staticmethod
    def _is_active(
        incident: TrafficIncident,
        now: datetime,
    ) -> bool:
        """
        Determine whether an incident is currently active.
        """

        if (
            incident.start_time is not None
            and now < incident.start_time
        ):
            return False

        if (
            incident.end_time is not None
            and now > incident.end_time
        ):
            return False

        return True

    @staticmethod
    def _blocks_routing(
        incident: TrafficIncident,
    ) -> bool:
        """
        Determine whether an incident should remove a road
        from the routing graph.

        Initially we treat high-severity incidents as blocking.

        This should eventually become configurable based on
        IncidentType.
        """

        return incident.severity >= 1.0

    # =============================================================
    # Graph helpers
    # =============================================================

    @staticmethod
    def _edge_identifiers(
        data: dict,
    ) -> list[str]:
        """
        Extract OSM road identifiers from an edge.

        Handles both:

            name = "PIE"

        and:

            ref = ["ECP", "PIE"]
        """

        identifiers = []

        for field in (
            data.get("name"),
            data.get("ref"),
        ):

            if isinstance(field, list):

                identifiers.extend(
                    str(value).lower()
                    for value in field
                    if value
                )

            elif field:

                identifiers.append(
                    str(field).lower()
                )

        return identifiers