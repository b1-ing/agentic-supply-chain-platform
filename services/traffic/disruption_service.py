from __future__ import annotations

from typing import Any

from models.traffic.traffic_incident import TrafficIncident


class DisruptionService:

    # ============================================================
    # FIND AFFECTED ROUTES
    # ============================================================

    def find_affected_routes(
        self,
        world,
        incident: TrafficIncident,
    ):
        """Find active routes whose route segments use the road affected by the

        incident.
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

    # ============================================================
    # DETERMINE WHETHER ROUTE IS AFFECTED
    # ============================================================

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

            nodes = getattr(
                segment,
                "nodes",
                [],
            )

            for u, v in zip(
                nodes,
                nodes[1:],
            ):

                edge = self._best_edge(
                    world.graph,
                    u,
                    v,
                )

                name = str(edge.get("name", "")).lower()

                ref = str(edge.get("ref", "")).lower()

                if target == name or target == ref:
                    return True

        return False

    # ============================================================
    # SHARED REROUTING METHOD
    # ============================================================

    async def reroute_route(
        self,
        world,
        route,
        vehicle,
        avoid_roads: list[str] | None = None,
        avoid_areas: list[str] | None = None,
    ) -> dict:

        avoid_roads = avoid_roads or []
        avoid_areas = avoid_areas or []

        if route is None:
            return {
                "success": False,
                "error": "Route is missing.",
            }

        if vehicle is None:
            return {
                "success": False,
                "error": "Vehicle is missing.",
            }

        from agents.tools.routing_tools import simple_routing_tool
        from models.order.routing_location import RoutingLocation
        from models.routing.route_segment import RouteSegment

        current_node = getattr(
            vehicle,
            "current_node",
            None,
        )

        current_lat = getattr(
            vehicle,
            "current_lat",
            None,
        )

        current_lon = getattr(
            vehicle,
            "current_lon",
            None,
        )

        if current_node is None:
            return {
                "success": False,
                "error": (
                    f"Vehicle {vehicle.vehicle_id} " "has no current graph node."
                ),
            }

        if current_lat is None or current_lon is None:
            return {
                "success": False,
                "error": (
                    f"Vehicle {vehicle.vehicle_id} " "has no current position."
                ),
            }

        stops = getattr(route, "stops", [])

        if not stops:
            return {
                "success": False,
                "error": "Route has no stops.",
            }

        completed_sequence = getattr(
            vehicle,
            "completed_stop_sequence",
            -1,
        )

        remaining_stops = [
            stop
            for stop in stops
            if getattr(stop, "sequence", -1) > completed_sequence
        ]

        if not remaining_stops:
            return {
                "success": False,
                "error": "No remaining stops to reroute.",
            }

        current_location = RoutingLocation(
            matrix_index=0,
            graph_node=current_node,
            lat=current_lat,
            lon=current_lon,
            kind="vehicle",
        )

        new_segments = []

        total_distance = 0.0
        total_travel_time = 0.0

        previous_location = current_location

        for stop in remaining_stops:

            location = stop.location

            result = simple_routing_tool.route_locations(
                world=world,
                origin=previous_location,
                destination=location,
                avoid_roads=avoid_roads,
                avoid_areas=avoid_areas,
            )

            if not result["success"]:
                return {
                    "success": False,
                    "error": (
                        f"Failed to reroute from "
                        f"{previous_location} to "
                        f"{location}: "
                        f"{result.get('error')}"
                    ),
                }

            route_data = result["route"]

            new_segment = RouteSegment(
                nodes=route_data["nodes"],
                geometry=route_data["geometry"],
                distance=route_data["distance_m"],
                travel_time=route_data["travel_time_s"],
                instructions=[],
            )

            new_segments.append(new_segment)

            total_distance += route_data["distance_m"]
            total_travel_time += route_data["travel_time_s"]

            previous_location = location

        # Replace route contents in-place.
        route.segments = new_segments
        route.total_distance = total_distance
        route.total_travel_time = total_travel_time

        # Restart simulation along the new route.
        vehicle.route_progress_m = 0.0

        vehicle.current_route = route
        vehicle.current_route_id = route.route_id

        return {
            "success": True,
            "route_id": route.route_id,
            "vehicle_id": vehicle.vehicle_id,
            "distance_m": total_distance,
            "travel_time_s": total_travel_time,
            "remaining_stop_count": len(remaining_stops),
            "avoid_roads": avoid_roads,
            "avoid_areas": avoid_areas,
        }

    # ============================================================
    # REROUTE ALL AFFECTED ROUTES
    # ============================================================

    async def reroute_affected_routes(
        self,
        world,
        incident: TrafficIncident,
    ) -> dict:
        """Find and reroute every active route affected by the traffic incident."""

        affected_routes = self.find_affected_routes(
            world=world,
            incident=incident,
        )

        results = []

        avoid_roads = [incident.road_name] if incident.road_name else []

        for route in affected_routes:

            vehicle = next(
                (
                    vehicle
                    for vehicle in world.vehicles
                    if vehicle.vehicle_id == route.vehicle_id
                ),
                None,
            )

            if vehicle is None:

                results.append(
                    {
                        "route_id": route.route_id,
                        "success": False,
                        "error": (f"Vehicle {route.vehicle_id} " "not found."),
                    }
                )

                continue

            result = await self.reroute_route(
                world=world,
                route=route,
                vehicle=vehicle,
                avoid_roads=avoid_roads,
            )

            results.append(result)

        return {
            "affected_route_count": len(affected_routes),
            "rerouted_route_count": sum(
                1 for result in results if result.get("success")
            ),
            "results": results,
        }

    # ============================================================
    # MULTI-EDGE SUPPORT
    # ============================================================

    def _best_edge(
        self,
        graph,
        u,
        v,
    ):
        """Return the best edge between two nodes.

        For MultiDiGraph, multiple parallel edges may exist. Select the edge
        with the lowest travel time.
        """

        edges = graph.get_edge_data(
            u,
            v,
        )

        if not edges:
            raise ValueError(f"No edge exists between graph nodes {u} and {v}")

        return min(
            edges.values(),
            key=lambda edge: edge.get(
                "travel_time",
                float("inf"),
            ),
        )