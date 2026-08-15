from __future__ import annotations

import networkx as nx
from uuid import uuid4

from models.order.routing_location import RoutingLocation
from models.routing.route_plan import RoutePlan
from models.routing.route_segment import RouteSegment
from models.routing.route_stop import RouteStop
from models.routing.travel_matrix import TravelMatrix
from models.routing.vehicle_route import VehicleRoute
from models.vehicles.vehicle import Vehicle
from models.vehicles.vehicle import VehicleStatus


class RouteBuilder:
    """
    Converts the raw OR-Tools solution into domain routing models.

    OR-Tools produces matrix-index routes such as:

        [
            [0, 3, 5, 0],
            [1, 4, 2, 1],
        ]

    RouteBuilder converts these into:

        RoutePlan
            ├── VehicleRoute
            │     ├── RouteStops
            │     └── RouteSegments
            └── VehicleRoute

    Important:
    ----------
    OR-Tools optimises using the WorldState routing graph.

    Therefore this class also reconstructs route geometry and metrics
    from that same graph rather than calling an external routing
    provider such as OneMap.
    """

    def build(
        self,
        world,
        travel_matrix: TravelMatrix,
        vehicles: list[Vehicle],
        routes: list[list[int]],
    ) -> RoutePlan:
        """
        Convert OR-Tools routes into a RoutePlan.

        Args:
            world:
                Current WorldState containing the routing graph.

            travel_matrix:
                Matrix and RoutingLocation mapping used by OR-Tools.

            vehicles:
                Vehicles corresponding to the OR-Tools vehicle indices.

            routes:
                Raw matrix-index routes returned by OR-Tools.

        Returns:
            RoutePlan containing all non-empty vehicle routes.
        """

        vehicle_routes: list[VehicleRoute] = []

        for vehicle, route in zip(vehicles, routes):

            vehicle_route = self._build_vehicle_route(
                world=world,
                travel_matrix=travel_matrix,
                vehicle=vehicle,
                route=route,
            )

            if vehicle_route is None:
                continue

            vehicle_routes.append(vehicle_route)

            # -----------------------------------------------------
            # Assign orders to the vehicle
            # -----------------------------------------------------

            self._assign_orders(
                world=world,
                vehicle=vehicle,
                stops=vehicle_route.stops,
            )

        return RoutePlan(
            routes=vehicle_routes,
            total_distance=sum(
                route.total_distance
                for route in vehicle_routes
            ),
            total_travel_time=sum(
                route.total_travel_time
                for route in vehicle_routes
            ),
        )

    # =============================================================
    # Vehicle Route
    # =============================================================

    def _build_vehicle_route(
        self,
        world,
        travel_matrix: TravelMatrix,
        vehicle: Vehicle,
        route: list[int],
    ) -> VehicleRoute | None:
        """
        Build a VehicleRoute from one OR-Tools vehicle route.

        Empty routes such as:

            [0, 0]

        are ignored.
        """

        if len(route) < 2:
            return None

        stops = self._build_stops(
            travel_matrix=travel_matrix,
            route=route,
        )

        if len(stops) < 2:
            return None

        segments = self._build_segments(
            world=world,
            stops=stops,
        )

        if not segments:
            return None

        total_distance = sum(
            segment.distance
            for segment in segments
        )

        total_travel_time = sum(
            segment.travel_time
            for segment in segments
        )

        if total_distance <= 0:
            return None

        route_id = f"ROUTE-{uuid4().hex[:8].upper()}"

        vehicle_route = VehicleRoute(
            route_id=route_id,
            vehicle_id=vehicle.vehicle_id,
            stops=stops,
            segments=segments,
            total_distance=total_distance,
            total_travel_time=total_travel_time,
        )

        # ---------------------------------------------------------
        # Update vehicle operational state
        # ---------------------------------------------------------

        vehicle.current_route_id = route_id
        vehicle.current_route = vehicle_route
        vehicle.status = VehicleStatus.EN_ROUTE

        return vehicle_route

    # =============================================================
    # Stops
    # =============================================================

    def _build_stops(
        self,
        travel_matrix: TravelMatrix,
        route: list[int],
    ) -> list[RouteStop]:
        """
        Convert matrix indices into RouteStop objects.
        """

        stops: list[RouteStop] = []

        for sequence, matrix_index in enumerate(route):

            if matrix_index < 0:
                raise ValueError(
                    f"Invalid negative matrix index: {matrix_index}"
                )

            if matrix_index >= len(travel_matrix.locations):
                raise IndexError(
                    f"Matrix index {matrix_index} is outside "
                    f"the location list."
                )

            location = travel_matrix.locations[matrix_index]

            stops.append(
                RouteStop(
                    sequence=sequence,
                    location=location,
                )
            )

        return stops

    # =============================================================
    # Segments
    # =============================================================

    ####################################################################
    # Segments
    ####################################################################

    def _build_segments(
        self,
        world,
        stops: list[RouteStop],
    ) -> list[RouteSegment]:

        segments: list[RouteSegment] = []

        if len(stops) < 2:
            return segments

        for current, nxt in zip(stops, stops[1:]):

            segment = self._build_segment(
                world,
                current.location,
                nxt.location,
            )

            segments.append(segment)

        return segments

    def _build_segment(
        self,
        world,
        from_location: RoutingLocation,
        to_location: RoutingLocation,
    ) -> RouteSegment:
        """
        Build a detailed route segment using the WorldState graph.

        OR-Tools determines the sequence of stops.
        This method determines the actual road-level path
        between each pair of stops.
        """

        if from_location.graph_node is None:
            raise ValueError(
                "Origin routing location has no graph node."
            )

        if to_location.graph_node is None:
            raise ValueError(
                "Destination routing location has no graph node."
            )

        graph = world.graph

        # ---------------------------------------------------------
        # Find shortest path on WorldState graph
        # ---------------------------------------------------------

        try:
            path = nx.shortest_path(
                graph,
                from_location.graph_node,
                to_location.graph_node,
                weight="travel_time",
            )

        except nx.NetworkXNoPath as exc:
            raise RuntimeError(
                f"No route between graph nodes "
                f"{from_location.graph_node} and "
                f"{to_location.graph_node}."
            ) from exc

        # ---------------------------------------------------------
        # Build metrics + geometry
        # ---------------------------------------------------------

        total_distance = 0.0
        total_travel_time = 0.0

        geometry = []

        for u, v in zip(path, path[1:]):

            edge = self._best_edge(
                graph,
                u,
                v,
            )

            total_distance += float(
                edge.get(
                    "length",
                    edge.get("distance", 0.0),
                )
            )

            total_travel_time += float(
                edge.get(
                    "travel_time",
                    0.0,
                )
            )

            edge_geometry = edge.get("geometry")

            if edge_geometry is not None:

                coords = list(
                    edge_geometry.coords
                )

                if geometry:
                    geometry.extend(
                        coords[1:]
                    )
                else:
                    geometry.extend(coords)

            else:

                # Fallback when OSM edge has no geometry.
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

                if not geometry:
                    geometry.append(u_coord)

                geometry.append(v_coord)

        return RouteSegment(
            nodes=path,
            geometry=geometry,
            distance=total_distance,
            travel_time=total_travel_time,
            instructions=[],
        )

    # =============================================================
    # Order assignment
    # =============================================================

    def _assign_orders(
        self,
        world,
        vehicle: Vehicle,
        stops: list[RouteStop],
    ) -> None:
        """
        Assign every order appearing in this vehicle's route to
        the vehicle.

        Pickup and delivery locations contain order_id, allowing
        us to determine which orders OR-Tools assigned to this
        vehicle.
        """

        order_ids: set[str] = set()

        for stop in stops:

            location = stop.location

            if (
                location.order_id
                and location.kind in {
                    "pickup",
                    "delivery",
                }
            ):
                order_ids.add(
                    location.order_id
                )

        if not order_ids:
            return

        for order in world.new_orders:

            if order.order_id in order_ids:
                order.assigned_vehicle = (
                    vehicle.vehicle_id
                )

    # =============================================================
    # Graph helpers
    # =============================================================

    @staticmethod
    def _best_edge(
        graph,
        u,
        v,
    ):
        """
        Return the fastest edge between two nodes.

        Supports both:

            DiGraph
            MultiDiGraph
        """

        edge_data = graph.get_edge_data(
            u,
            v,
        )

        if edge_data is None:
            raise RuntimeError(
                f"No edge exists between {u} and {v}."
            )

        # ---------------------------------------------------------
        # Standard DiGraph
        # ---------------------------------------------------------

        if "travel_time" in edge_data:
            return edge_data

        # ---------------------------------------------------------
        # MultiDiGraph
        # ---------------------------------------------------------

        return min(
            edge_data.values(),
            key=lambda edge: edge.get(
                "travel_time",
                float("inf"),
            ),
        )