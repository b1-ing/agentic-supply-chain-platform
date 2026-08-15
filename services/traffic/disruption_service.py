from __future__ import annotations

from models.traffic.traffic_incident import TrafficIncident
from uuid import uuid4

import networkx as nx

from models.routing.route_segment import RouteSegment
from models.routing.vehicle_route import VehicleRoute


class DisruptionService:

    # =========================================================
    # FIND AFFECTED ROUTES
    # =========================================================

    def find_affected_routes(
        self,
        world,
        incident: TrafficIncident,
    ):
        """
        Find active routes whose path uses the road affected
        by the traffic incident.
        """

        affected = []

        for route in world.routes:

            if self._route_affected(
                world,
                route,
                incident,
            ):
                affected.append(route)

        return affected

    # =========================================================
    # CHECK WHETHER ROUTE IS AFFECTED
    # =========================================================

    def _route_affected(
        self,
        world,
        route,
        incident: TrafficIncident,
    ) -> bool:

        if not incident.road_name:
            return False

        target = incident.road_name.strip().lower()

        for segment in route.segments:

            # RouteSegment should contain the graph nodes
            # used to construct this segment.
            nodes = getattr(segment, "nodes", None)

            if not nodes:
                continue

            for u, v in zip(nodes, nodes[1:]):

                edge = self._best_edge(
                    world.graph,
                    u,
                    v,
                )

                identifiers = self._edge_identifiers(edge)

                if self._matches_road(
                    target,
                    identifiers,
                ):
                    return True

        return False

    # =========================================================
    # REROUTE AFFECTED ROUTES
    # =========================================================

    def reroute_affected_routes(
        self,
        world,
        incident: TrafficIncident,
    ) -> dict:

        affected_routes = self.find_affected_routes(
            world=world,
            incident=incident,
        )

        if not affected_routes:
            return {
                "affected_route_count": 0,
                "rerouted_route_count": 0,
                "failed_route_count": 0,
                "rerouted_routes": [],
                "failed_routes": [],
            }

        rerouted_routes = []
        failed_routes = []

        for route in affected_routes:

            result = self._reroute_route(
                world=world,
                route=route,
                incident=incident,
            )

            if result["success"]:
                rerouted_routes.append(result)
            else:
                failed_routes.append(result)

        return {
            "affected_route_count": len(affected_routes),
            "rerouted_route_count": len(rerouted_routes),
            "failed_route_count": len(failed_routes),
            "rerouted_routes": rerouted_routes,
            "failed_routes": failed_routes,
        }

    # =========================================================
    # REROUTE ONE ROUTE
    # =========================================================

    def _reroute_route(
        self,
        world,
        route,
        incident: TrafficIncident,
    ) -> dict:

        vehicle = next(
            (
                vehicle
                for vehicle in world.vehicles
                if vehicle.vehicle_id == route.vehicle_id
            ),
            None,
        )

        if vehicle is None:
            return {
                "success": False,
                "route_id": route.route_id,
                "error": (
                    f"Vehicle '{route.vehicle_id}' "
                    "not found."
                ),
            }

        if vehicle.current_node is None:
            return {
                "success": False,
                "route_id": route.route_id,
                "vehicle_id": route.vehicle_id,
                "error": (
                    "Vehicle has no current graph node."
                ),
            }

        # -----------------------------------------------------
        # Build restricted graph
        # -----------------------------------------------------

        graph = world.graph.copy()

        removed_edges = self._remove_incident_edges(
            graph,
            incident,
        )

        # -----------------------------------------------------
        # Determine remaining stops
        # -----------------------------------------------------

        remaining_stops = self._remaining_stops(
            route,
        )

        if not remaining_stops:
            return {
                "success": False,
                "route_id": route.route_id,
                "vehicle_id": route.vehicle_id,
                "error": "No remaining stops to reroute.",
            }

        # -----------------------------------------------------
        # Route from vehicle's current position
        # through remaining stops
        # -----------------------------------------------------

        previous_node = vehicle.current_node

        new_segments = []

        total_distance = 0.0
        total_travel_time = 0.0

        for stop in remaining_stops:

            destination_node = (
                stop.location.graph_node
            )

            if destination_node is None:
                return {
                    "success": False,
                    "route_id": route.route_id,
                    "vehicle_id": route.vehicle_id,
                    "error": (
                        f"Stop {stop.sequence} has "
                        "no graph node."
                    ),
                }

            try:

                path = nx.shortest_path(
                    graph,
                    previous_node,
                    destination_node,
                    weight="travel_time",
                )

            except nx.NetworkXNoPath:

                return {
                    "success": False,
                    "route_id": route.route_id,
                    "vehicle_id": route.vehicle_id,
                    "error": (
                        f"No route exists from node "
                        f"{previous_node} to "
                        f"{destination_node} after "
                        "applying the traffic restriction."
                    ),
                }

            segment = self._build_segment(
                graph,
                path,
            )

            new_segments.append(segment)

            total_distance += segment.distance
            total_travel_time += segment.travel_time

            previous_node = destination_node

        # -----------------------------------------------------
        # Build new VehicleRoute
        # -----------------------------------------------------

        new_route_id = (
            f"ROUTE-{uuid4().hex[:8].upper()}"
        )

        new_route = VehicleRoute(
            route_id=new_route_id,
            vehicle_id=vehicle.vehicle_id,
            stops=remaining_stops,
            segments=new_segments,
            total_distance=total_distance,
            total_travel_time=total_travel_time,
        )

        # -----------------------------------------------------
        # Replace old route
        # -----------------------------------------------------

        world.routes = [
            existing
            for existing in world.routes
            if existing.route_id != route.route_id
        ]

        world.routes.append(new_route)

        vehicle.current_route_id = new_route_id
        vehicle.current_route = new_route

        return {
            "success": True,
            "old_route_id": route.route_id,
            "new_route_id": new_route_id,
            "vehicle_id": vehicle.vehicle_id,
            "distance_m": total_distance,
            "travel_time_s": total_travel_time,
            "removed_edges": removed_edges,
        }

    # =========================================================
    # REMOVE INCIDENT ROAD
    # =========================================================

    def _remove_incident_edges(
        self,
        graph,
        incident: TrafficIncident,
    ) -> int:

        if not incident.road_name:
            return 0

        target = incident.road_name.strip().lower()

        removed = 0

        for u, v, key, data in list(
            graph.edges(
                keys=True,
                data=True,
            )
        ):

            identifiers = self._edge_identifiers(
                data,
            )

            if self._matches_road(
                target,
                identifiers,
            ):

                graph.remove_edge(
                    u,
                    v,
                    key,
                )

                removed += 1

        return removed

    # =========================================================
    # REMAINING STOPS
    # =========================================================

    def _remaining_stops(
        self,
        route,
    ):

        """
        Return stops that have not yet been completed.

        This assumes the route's stop sequence represents the
        operational order and that completed stops are marked
        using a `completed` attribute.

        Adjust this if your RouteStop model uses a different
        completion representation.
        """

        return [
            stop
            for stop in route.stops
            if not getattr(
                stop,
                "completed",
                False,
            )
        ]

    # =========================================================
    # BUILD ROUTE SEGMENT
    # =========================================================

    def _build_segment(
        self,
        graph,
        path,
    ) -> RouteSegment:

        total_distance = 0.0
        total_time = 0.0

        geometry_coords = []

        for u, v in zip(
            path,
            path[1:],
        ):

            edge = self._best_edge(
                graph,
                u,
                v,
            )

            total_distance += float(
                edge.get(
                    "length",
                    edge.get(
                        "distance",
                        0.0,
                    ),
                )
            )

            total_time += float(
                edge.get(
                    "travel_time",
                    0.0,
                )
            )

            edge_geometry = edge.get(
                "geometry"
            )

            if edge_geometry is not None:

                coords = list(
                    edge_geometry.coords
                )

                if geometry_coords:
                    geometry_coords.extend(
                        coords[1:]
                    )
                else:
                    geometry_coords.extend(
                        coords
                    )

            else:

                u_data = graph.nodes[u]
                v_data = graph.nodes[v]

                u_coord = (
                    u_data["x"],
                    u_data["y"],
                )

                v_coord = (
                    v_data["x"],
                    v_data["y"],
                )

                if not geometry_coords:
                    geometry_coords.append(
                        u_coord
                    )

                geometry_coords.append(
                    v_coord
                )

        return RouteSegment(
            nodes=path,
            geometry=geometry_coords,
            distance=total_distance,
            travel_time=total_time,
            instructions=[],
        )

    # =========================================================
    # EDGE HELPERS
    # =========================================================

    def _best_edge(
        self,
        graph,
        u,
        v,
    ):

        edges = graph.get_edge_data(
            u,
            v,
        )

        if not edges:
            raise ValueError(
                f"No edge exists between "
                f"graph nodes {u} and {v}"
            )

        return min(
            edges.values(),
            key=lambda edge: edge.get(
                "travel_time",
                float("inf"),
            ),
        )

    def _edge_identifiers(
        self,
        edge,
    ) -> list[str]:

        identifiers = []

        for field in (
            "name",
            "ref",
        ):

            value = edge.get(field)

            if isinstance(value, list):

                identifiers.extend(
                    str(item).strip().lower()
                    for item in value
                    if item
                )

            elif value:

                identifiers.append(
                    str(value).strip().lower()
                )

        return identifiers

    def _matches_road(
        self,
        target: str,
        identifiers: list[str],
    ) -> bool:

        return any(
            target == identifier
            or target in identifier
            for identifier in identifiers
        )