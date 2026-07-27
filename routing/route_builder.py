from __future__ import annotations

import networkx as nx

from models.route_plan import RoutePlan
from models.route_segment import RouteSegment
from models.route_stop import RouteStop
from models.travel_matrix import TravelMatrix
from models.vehicle_route import VehicleRoute
from models.vehicles.vehicle import Vehicle


class RouteBuilder:
    """Converts the raw OR-Tools solution into domain models.

    OR-Tools output:
        [
            [0, 3, 5, 0],
            [1, 4, 2, 1],
        ]

    becomes:
        RoutePlan
            ├── VehicleRoute
            │     ├── RouteStops
            │     └── RouteSegments
            └── VehicleRoute
    """

    def build(
        self,
        world,
        travel_matrix: TravelMatrix,
        vehicles: list[Vehicle],
        routes: list[list[int]],
    ) -> RoutePlan:
        """Constructs a complete RoutePlan from raw optimization routes.

        Args:
            world: The world context containing the underlying routing graph.
            travel_matrix: The distance/time matrix mapping locations to indices.
            vehicles: A list of Vehicle objects assigned to the routes.
            routes: A list of lists, where each sublist contains the sequence of
                matrix indices representing a vehicle's route.

        Returns:
            A fully populated RoutePlan containing the routes for all vehicles
            along with combined total distances and travel times.

            RoutePlan consists of:
                routes: list[VehicleRoute] (list of the routes of all vehicles)
                total_distance: float
                total_travel_time: float

        """
        vehicle_routes: list[VehicleRoute] = []

        for vehicle, route in zip(vehicles, routes):
            vehicle_route = self._build_vehicle_route(
                world,
                travel_matrix,
                vehicle,
                route,
            )

            vehicle_routes.append(vehicle_route)

        return RoutePlan(
            routes=vehicle_routes,
            total_distance=sum(route.total_distance for route in vehicle_routes),
            total_travel_time=sum(route.total_travel_time for route in vehicle_routes),
        )

    ####################################################################
    # Vehicle Route
    ####################################################################

    def _build_vehicle_route(
        self,
        world,
        travel_matrix: TravelMatrix,
        vehicle: Vehicle,
        route: list[int],
    ) -> VehicleRoute:
        """Builds a high-level route for a specific vehicle.

        Args:
            world: The world context containing the underlying routing graph.
            travel_matrix: The matrix mapping indices to geographical locations.
            vehicle: The Vehicle instance executing this route.
            route: The sequence of matrix indices representing stops.

        Returns:
            A VehicleRoute domain object containing stops, detailed street-network
            segments, and accumulated metrics.

            VehicleRoute consists of:
            vehicle_id: str (identifies the vehicle)
            stops: list[RouteStop]
            segments: list[RouteSegment]
            total_distance
            total_travel_time

        """
        stops = self._build_stops(
            travel_matrix,
            route,
        )

        segments = self._build_segments(
            world,
            stops,
        )

        # the below are self explanatory, calculating distance and travel times from each segments only
        total_distance = sum(segment.distance for segment in segments)

        total_travel_time = sum(segment.travel_time for segment in segments)

        return VehicleRoute(
            vehicle_id=vehicle.vehicle_id,
            stops=stops,
            segments=segments,
            total_distance=total_distance,
            total_travel_time=total_travel_time,
        )

    ####################################################################
    # Stops
    ####################################################################

    def _build_stops(
        self,
        travel_matrix: TravelMatrix,
        route: list[int],
    ) -> list[RouteStop]:
        """Maps raw matrix route indices to a sequence of domain RouteStop objects.

        Args:
            travel_matrix: The matrix mapping indices to geographical locations.
            route: The ordered sequence of matrix indices.

        Returns:
            A list of RouteStop objects with assigned sequences and location data.

            RouteStop object consists of:
            sequence:int
            location: RoutingLocation
            arrival_time
            departure_time
            load_after_stop
        """
        stops: list[RouteStop] = []

        for sequence, matrix_index in enumerate(route):
            location = travel_matrix.locations[matrix_index]

            stops.append(
                RouteStop(
                    sequence=sequence,
                    location=location,
                )
            )

        return stops

    ####################################################################
    # Segments
    ####################################################################

    def _build_segments(
        self,
        world,
        stops: list[RouteStop],
    ) -> list[RouteSegment]:
        """Generates detailed street-level route segments between all sequential stops.

        Args:
            world: The world context containing the underlying routing graph.
            stops: A list of RouteStop objects representing the visited locations.

        Returns:
            A list of RouteSegment objects connecting the stops. Returns an empty
            list if there are fewer than two stops.
        """
        segments: list[RouteSegment] = []

        if len(stops) < 2:
            return segments

        for current, nxt in zip(
            stops,
            stops[1:],
        ):
            segment = self._build_segment(
                world,
                current.location.graph_node,
                nxt.location.graph_node,
            )

            segments.append(segment)

        return segments

    def _build_segment(
        self,
        world,
        from_node: int,
        to_node: int,
    ) -> RouteSegment:
        """Calculates the shortest street-network path and costs between two graph nodes.

        Calculates the fastest route using NetworkX, extracts geometry coordinates,
        and sums up distance and travel time from the chosen edges.

        Args:
            world: The world context containing the underlying routing graph.
            from_node: The starting NetworkX graph node ID.
            to_node: The destination NetworkX graph node ID.

        Returns:
            A detailed RouteSegment object containing the path, shape coordinates,
            and aggregate costs.
        """
        graph = world.graph

        path = nx.shortest_path(
            graph,
            source=from_node,
            target=to_node,
            weight="travel_time",
        )

        travel_time = 0.0
        distance = 0.0

        geometry: list[tuple[float, float]] = []

        ###############################################################
        # Build geometry
        ###############################################################
        print("path:", path)
        for node in path:
            print("node:", graph.nodes[0])

            geometry.append(
                (
                    graph.nodes[node]["y"],  # latitude
                    graph.nodes[node]["x"],  # longitude
                )
            )

        ###############################################################
        # Sum edge costs
        ###############################################################

        for u, v in zip(path, path[1:]):
            edge = self._best_edge(
                graph,
                u,
                v,
            )

            travel_time += edge.get(
                "travel_time",
                0,
            )

            distance += edge.get(
                "length",
                0,
            )

        return RouteSegment(
            from_node=from_node,
            to_node=to_node,
            graph_path=path,
            geometry=geometry,
            travel_time=travel_time,
            distance=distance,
        )

    ####################################################################
    # Helpers
    ####################################################################

    @staticmethod
    def _best_edge(
        graph,
        u,
        v,
    ):
        """Retrieves the edge data between two nodes, choosing the fastest if duplicates exist.

        Supports both standard NetworkX DiGraph and MultiDiGraph structures. For
        parallel edges in a MultiDiGraph, it selects the edge with the lowest
        `travel_time`.

        Args:
            graph: The NetworkX graph containing the edge.
            u: The source node ID.
            v: The target node ID.

        Returns:
            dict: The dictionary containing the chosen edge's properties.

        Raises:
            RuntimeError: If no edge exists between node `u` and node `v`.
        """
        edge = graph.get_edge_data(u, v)

        if edge is None:
            raise RuntimeError(f"No edge exists between {u} and {v}")

        if "travel_time" in edge:
            return edge

        return min(
            edge.values(),
            key=lambda e: e.get(
                "travel_time",
                float("inf"),
            ),
        )
