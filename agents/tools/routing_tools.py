# agent/tools/routing_tools.py
from __future__ import annotations
from services.world.world_manager import world_manager
from services.routing.routing_service import RoutingService
from agents.tools.geocoding_tools import geocode_location
from uuid import uuid4
from models.order.routing_location import RoutingLocation
from models.routing.route_segment import RouteSegment
from models.routing.vehicle_route import VehicleRoute
from models.routing.route_stop import RouteStop
from models.vehicles.vehicle import VehicleStatus
from services.routing.compatibility_service import CompatibilityService
from models.routing.compatibility_result import CompatibilityStatus
from typing import Any
import re
import networkx as nx
import osmnx as ox
from services.world.world_manager import world_manager
from services.routing.onemap_routing_service import OneMapRoutingService


class SimpleRoutingTool:
    """
    Point-to-point routing tool.

    The LLM supplies natural-language routing constraints.
    This tool resolves the locations and performs the actual routing.

    This tool does NOT:
    - assign vehicles
    - modify orders
    - run CVRP
    - modify WorldState
    """

    def __init__(self):
        self.onemap = OneMapRoutingService()

    def route(
        self,
        origin: str,
        destination: str,
        avoid_roads: list[str] | None = None,
        avoid_areas: list[str] | None = None,
        required_waypoints: list[str] | None = None,
    ) -> dict[str, Any]:

        avoid_roads = avoid_roads or []
        avoid_areas = avoid_areas or []
        required_waypoints = required_waypoints or []

        world = world_manager.get_world()

        # ---------------------------------------------------------
        # Resolve origin and destination
        # ---------------------------------------------------------

        origin_location = self._resolve_location(
            world,
            origin,
        )
        if origin_location is None:

            result = geocode_location(origin)

            if not result["success"]:
                return result

            origin_location = RoutingLocation(
                    matrix_index=0,
                    graph_node=ox.distance.nearest_nodes(
                        world.graph,
                        result["longitude"],
                        result["latitude"],
                    ),
                    lat=result["latitude"],
                    lon=result["longitude"],
                    kind="routing",
                )

        destination_location = self._resolve_location(
            world,
            destination,
        )
        if destination_location is None:

            result = geocode_location(destination)

            if not result["success"]:
                return result

            destination_location = RoutingLocation(
                    matrix_index=0,
                    graph_node=ox.distance.nearest_nodes(
                        world.graph,
                        result["longitude"],
                        result["latitude"],
                    ),
                    lat=result["latitude"],
                    lon=result["longitude"],
                    kind="routing",
                )


        # ---------------------------------------------------------
        # Resolve waypoints
        # ---------------------------------------------------------

        waypoint_locations = []

        for waypoint in required_waypoints:

            location = self._resolve_location(
                world,
                waypoint,
            )

            if location is None:
                return {
                    "success": False,
                    "error": f"Could not resolve waypoint: {waypoint}",
                }

            waypoint_locations.append(location)

        # ---------------------------------------------------------
        # Check whether constraints can be applied
        # ---------------------------------------------------------

        if avoid_roads or avoid_areas:
            return self._route_with_constraints(
                world=world,
                origin=origin_location,
                destination=destination_location,
                waypoints=waypoint_locations,
                avoid_roads=avoid_roads,
                avoid_areas=avoid_areas,
            )

        # ---------------------------------------------------------
        # Simple OneMap routing
        # ---------------------------------------------------------
        print(origin_location, destination_location)
#         route = self._route_onemap(
#             origin_location,
#             destination_location,
#         )

        return self._route_with_graph(
            world=world,
            origin=origin_location,
            destination=destination_location,
            waypoints=waypoint_locations,
            avoid_roads=avoid_roads,
            avoid_areas=avoid_areas,
        )

    def _route_with_graph(
        self,
        world,
        origin: dict,
        destination: dict,
        waypoints: list[dict],
        avoid_roads: list[str],
        avoid_areas: list[str],
    ) -> dict[str, Any]:

        graph = world.graph

        # ---------------------------------------------------------
        # Snap origin/destination to OSM graph
        # ---------------------------------------------------------

        origin_node = ox.distance.nearest_nodes(
            graph,
            X=origin.lon,
            Y=origin.lat,
        )

        destination_node = ox.distance.nearest_nodes(
            graph,
            X=destination.lon,
            Y=destination.lat,
        )

        # ---------------------------------------------------------
        # Resolve waypoints
        # ---------------------------------------------------------

        waypoint_nodes = []

        for waypoint in waypoints:
            node = ox.distance.nearest_nodes(
                graph,
                X=waypoint["lon"],
                Y=waypoint["lat"],
            )

            waypoint_nodes.append(node)

        # ---------------------------------------------------------
        # Apply temporary restrictions
        # ---------------------------------------------------------

        routing_graph = graph.copy()

        removed_edges = []

        if avoid_roads or avoid_areas:

            removed_edges = self._remove_restricted_edges(
                routing_graph,
                avoid_roads=avoid_roads,
                avoid_areas=avoid_areas,
            )

        # ---------------------------------------------------------
        # Build complete sequence
        # ---------------------------------------------------------

        targets = (
            waypoint_nodes
            + [destination_node]
        )

        current_node = origin_node

        full_path = []

        total_distance = 0.0
        total_travel_time = 0.0

        # ---------------------------------------------------------
        # Route each leg
        # ---------------------------------------------------------

        for target_node in targets:

            path = ox.routing.shortest_path(
                routing_graph,
                current_node,
                target_node,
                weight="travel_time",
            )

            if path is None:
                return {
                    "success": False,
                    "error": (
                        f"No route from node "
                        f"{current_node} to {target_node}"
                    ),
                }

            if full_path:
                full_path.extend(path[1:])
            else:
                full_path.extend(path)

            geometry = []

            for u, v in zip(full_path, full_path[1:]):
                edge = self._best_edge(world.graph, u, v)

                if "geometry" in edge:
                    coords = list(edge["geometry"].coords)

                    if geometry:
                        geometry.extend(coords[1:])
                    else:
                        geometry.extend(coords)
                else:
                    geometry.append((
                        world.graph.nodes[u]["x"],
                        world.graph.nodes[u]["y"],
                    ))

            # Add final node
            if full_path:
                geometry.append((
                    world.graph.nodes[full_path[-1]]["x"],
                    world.graph.nodes[full_path[-1]]["y"],
                ))

            leg_edges = ox.routing.route_to_gdf(
                routing_graph,
                path,
                weight="travel_time",
            )

            total_distance += float(
                leg_edges["length"].sum()
            )

            total_travel_time += float(
                leg_edges["travel_time"].sum()
            )

            current_node = target_node

        return {
            "success": True,
            "routing_mode": "graph",
            "origin": origin["name"],
            "destination": destination["name"],
            "route": {
                "nodes": full_path,
                "geometry": geometry,
                "distance_m": total_distance,
                "travel_time_s": total_travel_time,
                "avoid_roads": avoid_roads,
                "avoid_areas": avoid_areas,
                "removed_edges": len(removed_edges),
            },
        }

    # =============================================================
    # Location resolution
    # =============================================================

    def _resolve_location(
        self,
        world,
        place: str,
    ):
        """
        Resolve a place name into a routing location.

        First tries known locations in WorldState.

        You can later replace/extend this with your geocoding service.
        """

        place_normalized = place.strip().lower()

        # ---------------------------------------------------------
        # Existing orders
        # ---------------------------------------------------------

        for order in world.orders_in_progress:

            for address, lat, lon in [
                (
                    order.pickup_address,
                    order.pickup_lat,
                    order.pickup_lon,
                ),
                (
                    order.delivery_address,
                    order.delivery_lat,
                    order.delivery_lon,
                ),
            ]:

                if (
                    address
                    and address.strip().lower()
                    == place_normalized
                    and lat is not None
                    and lon is not None
                ):
                    return {
                        "name": address,
                        "lat": float(lat),
                        "lon": float(lon),
                    }

        # ---------------------------------------------------------
        # New orders
        # ---------------------------------------------------------

        for order in world.new_orders:

            for address, lat, lon in [
                (
                    order.pickup_address,
                    order.pickup_lat,
                    order.pickup_lon,
                ),
                (
                    order.delivery_address,
                    order.delivery_lat,
                    order.delivery_lon,
                ),
            ]:

                if (
                    address
                    and address.strip().lower()
                    == place_normalized
                    and lat is not None
                    and lon is not None
                ):
                    return {
                        "name": address,
                        "lat": float(lat),
                        "lon": float(lon),
                    }

        return None

    # =============================================================
    # OneMap
    # =============================================================

    def _route_onemap(
        self,
        origin,
        destination,
    ):

        return self.onemap.route(
            start_lat=origin["lat"],
            start_lon=origin["lon"],
            end_lat=destination["lat"],
            end_lon=destination["lon"],
        )

    # =============================================================
    # Constrained routing
    # =============================================================


    def _route_with_constraints(
        self,
        world,
        origin,
        destination,
        waypoints,
        avoid_roads,
        avoid_areas,
    ):
        """
        Perform constrained routing using the WorldState graph.
        """
        graph = world.graph.copy()
        removed_edges = 0

        # 1. Pre-compile regex patterns for performance and strict word boundaries.
        #    \b ensures 'PIE' matches 'PIE' or 'PIE Expressway' but NOT 'Pier' or 'Spies'.
        avoid_patterns = [
            re.compile(r'\b' + re.escape(road.lower()) + r'\b')
            for road in avoid_roads if road.strip()
        ]


        # 2. Iterate and filter
        for u, v, key, data in list(graph.edges(keys=True, data=True)):

            # Extract both OSM 'name' and 'ref' (where expressways like PIE/AYE live)
            road_name = data.get("name", "")
            road_ref = data.get("ref", "")

            # Helper to normalize OSM's tendency to return lists or strings
            def extract_identifiers(field):
                if isinstance(field, list):
                    return [str(x).lower() for x in field if x]
                elif field:
                    return [str(field).lower()]
                return []

            # Combine names and refs into a single list of targets for this edge
            identifiers = extract_identifiers(road_name) + extract_identifiers(road_ref)

            # Check if any avoid pattern matches any identifier exactly
            should_avoid = any(
                pattern.search(identifier)
                for pattern in avoid_patterns
                for identifier in identifiers
            )

            if should_avoid:
                graph.remove_edge(u, v, key)
                removed_edges += 1


        # ---------------------------------------------------------
        # TODO:
        # Area constraints
        # ---------------------------------------------------------
        #
        # Once you have polygons for named areas, remove edges
        # whose geometry intersects those polygons.
        #
        # For now, explicitly report that they were not enforced.

        unresolved_area_constraints = list(avoid_areas)

        # ---------------------------------------------------------
        # Snap locations to graph
        # ---------------------------------------------------------

        origin_node = origin.graph_node
        destination_node = destination.graph_node

        if origin_node is None:
            return {
                "success": False,
                "error": "Could not map origin onto routing graph.",
            }

        if destination_node is None:
            return {
                "success": False,
                "error": "Could not map destination onto routing graph.",
            }

        # ---------------------------------------------------------
        # Route
        # ---------------------------------------------------------

        try:

            path = nx.shortest_path(
                graph,
                origin_node,
                destination_node,
                weight="travel_time",
            )

        except nx.NetworkXNoPath:

            return {
                "success": False,
                "error": (
                    "No route exists after applying "
                    "the requested road restrictions."
                ),
            }

        # ---------------------------------------------------------
        # Calculate metrics
        # ---------------------------------------------------------

        total_time = 0.0
        total_distance = 0.0

        geometry_coords = []

        for u, v in zip(path, path[1:]):

            edge = self._best_edge(
                graph,
                u,
                v,
            )

            total_time += float(
                edge.get("travel_time", 0.0)
            )

            total_distance += float(
                edge.get("length", 0.0)
            )

            # ---------------------------------------------
            # Extract road geometry
            # ---------------------------------------------

            edge_geometry = edge.get("geometry")

            if edge_geometry is not None:
                coords = list(edge_geometry.coords)

                # Avoid duplicating the connecting point
                if geometry_coords:
                    geometry_coords.extend(coords[1:])
                else:
                    geometry_coords.extend(coords)

            else:
                # Some OSM edges may not have explicit geometry.
                # Fall back to the node coordinates.
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
                    geometry_coords.append(u_coord)

                geometry_coords.append(v_coord)

        return {
            "success": True,
            "routing_mode": "graph",
            "route": {
                "nodes": path,
                "distance_m": total_distance,
                "geometry": geometry_coords,
                "travel_time_s": total_time,
                "avoid_roads": avoid_roads,
                "avoid_areas": avoid_areas,
                "removed_edges": removed_edges,
                "unresolved_area_constraints": (
                    unresolved_area_constraints
                ),
            },
        }

    # =============================================================
    # Graph helpers
    # =============================================================

    @staticmethod
    def _nearest_node(
        graph,
        lat: float,
        lon: float,
    ):
        """
        Find the nearest graph node to a coordinate.

        For now this uses a simple Euclidean search.
        Replace with a spatial index later if necessary.
        """

        if graph.number_of_nodes() == 0:
            return None

        best_node = None
        best_distance = float("inf")

        for node, data in graph.nodes(data=True):

            node_lat = data.get("y")
            node_lon = data.get("x")

            if node_lat is None or node_lon is None:
                continue

            distance = (
                (float(node_lat) - lat) ** 2
                + (float(node_lon) - lon) ** 2
            )

            if distance < best_distance:
                best_distance = distance
                best_node = node

        return best_node

    @staticmethod
    def _best_edge(
        graph,
        u,
        v,
    ):
        edge = graph.get_edge_data(
            u,
            v,
        )

        if edge is None:
            raise RuntimeError(
                f"No edge exists between {u} and {v}"
            )

        # DiGraph
        if "travel_time" in edge:
            return edge

        # MultiDiGraph
        return min(
            edge.values(),
            key=lambda e: e.get(
                "travel_time",
                float("inf"),
            ),
        )

    # =============================================================
    # Serialization
    # =============================================================

    @staticmethod
    def _serialize_route(route):

        return {
            "status_message": route.get(
                "status_message"
            ),
            "route_id": route.get(
                "route_id"
            ),
            "route_geometry": route.get(
                "route_geometry"
            ),
            "route_instructions": route.get(
                "route_instructions"
            ),
            "route_name": route.get(
                "route_name"
            ),
            "route_summary": route.get(
                "route_summary"
            ),
            "viaRoute": route.get(
                "viaRoute"
            ),
            "subtitle": route.get(
                "subtitle"
            ),
        }
    def route_locations(
        self,
        world,
        origin: RoutingLocation,
        destination: RoutingLocation,
        avoid_roads: list[str] | None = None,
        avoid_areas: list[str] | None = None,
        required_waypoints: list[str] | None = None,
    ) -> dict:
        """
        Route between already-resolved RoutingLocation objects.

        Unlike route(), this method does not geocode or resolve addresses.
        It uses the graph nodes already attached to the RoutingLocation objects.
        """

        avoid_roads = avoid_roads or []
        avoid_areas = avoid_areas or []
        required_waypoints = required_waypoints or []

        if origin.graph_node is None:
            return {
                "success": False,
                "error": "Origin has no graph node.",
            }

        if destination.graph_node is None:
            return {
                "success": False,
                "error": "Destination has no graph node.",
            }

        # ---------------------------------------------------------
        # Build waypoint locations
        # ---------------------------------------------------------

        waypoint_locations: list[RoutingLocation] = []

        for waypoint in required_waypoints:
            waypoint_location = self._resolve_location(
                world,
                waypoint,
            )

            if waypoint_location is None:
                return {
                    "success": False,
                    "error": f"Could not resolve required waypoint: {waypoint}",
                }

            waypoint_locations.append(waypoint_location)

        # ---------------------------------------------------------
        # Build ordered locations
        # ---------------------------------------------------------

        locations = [
            origin,
            *waypoint_locations,
            destination,
        ]

        # ---------------------------------------------------------
        # Apply routing constraints
        # ---------------------------------------------------------



        if avoid_roads or avoid_areas:
            return self._route_with_constraints(
                world=world,
                origin=origin,
                destination=destination,
                waypoints=waypoint_locations,
                avoid_roads=avoid_roads,
                avoid_areas=avoid_areas,
            )

        # ---------------------------------------------------------
        # Simple graph routing
        # ---------------------------------------------------------

        try:
            full_path: list[int] = []
            geometry_coords = []
            total_distance = 0.0
            total_travel_time = 0.0

            for current, nxt in zip(locations, locations[1:]):

                path = nx.shortest_path(
                    world.graph,
                    current.graph_node,
                    nxt.graph_node,
                    weight="travel_time",
                )

                if full_path:
                    full_path.extend(path[1:])
                else:
                    full_path.extend(path)

                for u, v in zip(path, path[1:]):
                    edge = self._best_edge(
                        world.graph,
                        u,
                        v,
                    )

                    total_distance += edge.get(
                        "length",
                        edge.get("distance", 0.0),
                    )

                    total_travel_time += edge.get(
                        "travel_time",
                        0.0,
                    )

                    edge_geometry = edge.get("geometry")

                    if edge_geometry is not None:
                        coords = list(edge_geometry.coords)

                        # Avoid duplicating the connecting point
                        if geometry_coords:
                            geometry_coords.extend(coords[1:])
                        else:
                            geometry_coords.extend(coords)

                    else:
                        # Some OSM edges may not have explicit geometry.
                        # Fall back to the node coordinates.
                        u_data = world.graph.nodes[u]
                        v_data = world.graph.nodes[v]

                        u_coord = (
                            u_data["x"],
                            u_data["y"],
                        )

                        v_coord = (
                            v_data["x"],
                            v_data["y"],
                        )

                        if not geometry_coords:
                            geometry_coords.append(u_coord)

                        geometry_coords.append(v_coord)

            return {
                "success": True,
                "routing_mode": "graph",
                "origin": origin,
                "destination": destination,
                "route": {
                    "nodes": full_path,
                    "geometry": geometry_coords,
                    "distance_m": total_distance,
                    "travel_time_s": total_travel_time,
                    "avoid_roads": avoid_roads,
                    "avoid_areas": avoid_areas,
                },
            }

        except nx.NetworkXNoPath:
            return {
                "success": False,
                "error": (
                    f"No route between graph nodes "
                    f"{origin.graph_node} and {destination.graph_node}."
                ),
            }


simple_routing_tool = SimpleRoutingTool()


def route_between_places(
    origin: str,
    destination: str,
    avoid_roads: list[str] | None = None,
    avoid_areas: list[str] | None = None,
    required_waypoints: list[str] | None = None,
) -> dict[str, Any]:

    print(
        "[ROUTING]",
        "origin:",
        origin,
    )

    print(
        "[ROUTING]",
        "destination:",
        destination,
    )

    return simple_routing_tool.route(
        origin=origin,
        destination=destination,
        avoid_roads=avoid_roads,
        avoid_areas=avoid_areas,
        required_waypoints=required_waypoints,
    )

routing_service = RoutingService()

def decide_routing_strategy(
    order_id: str,
) -> dict:
    """
    Decide whether an order should use simple routing
    or fleet-wide CVRP optimisation.
    """

    world = world_manager.get_world()

    order = next(
        (
            o for o in (
                world.new_orders
                + world.orders_in_progress
            )
            if o.order_id == order_id
        ),
        None,
    )

    if order is None:
        return {
            "success": False,
            "error": f"Order {order_id} not found.",
        }

    # ---------------------------------------------------------
    # Find the order's current assignment
    # ---------------------------------------------------------

    assigned_vehicle_id = getattr(
        order,
        "assigned_vehicle",
        None,
    )

    # ---------------------------------------------------------
    # SIMPLE ROUTING
    #
    # If this order already has a specific vehicle assigned,
    # there is no need for fleet-wide optimisation.
    # ---------------------------------------------------------

    if assigned_vehicle_id:
        return {
            "success": True,
            "order_id": order_id,
            "strategy": "SIMPLE",
            "reason": (
                f"Order is already assigned to vehicle "
                f"{assigned_vehicle_id}; only its route needs "
                f"to be computed."
            ),
        }

    # ---------------------------------------------------------
    # Count genuinely unassigned NEW orders.
    #
    # Orders already in progress have already been assigned
    # and should not automatically trigger CVRP.
    # ---------------------------------------------------------

    unassigned_orders = [
        o
        for o in world.new_orders
        if not getattr(o, "assigned_vehicle", None)
    ]

    # ---------------------------------------------------------
    # ONE UNASSIGNED ORDER
    #
    # If compatibility has already selected a vehicle, use
    # simple routing.
    # ---------------------------------------------------------

    if len(unassigned_orders) == 1:
        return {
            "success": True,
            "order_id": order_id,
            "strategy": "SIMPLE",
            "reason": (
                "Only one unassigned order requires routing; "
                "fleet-wide optimisation is unnecessary."
            ),
        }

    # ---------------------------------------------------------
    # MULTIPLE UNASSIGNED ORDERS
    #
    # This is where CVRP becomes useful.
    # ---------------------------------------------------------

    if len(unassigned_orders) > 1:
        return {
            "success": True,
            "order_id": order_id,
            "strategy": "CVRP",
            "reason": (
                f"{len(unassigned_orders)} unassigned orders "
                "require joint fleet assignment and routing."
            ),
        }

    # ---------------------------------------------------------
    # FALLBACK
    # ---------------------------------------------------------

    return {
        "success": True,
        "order_id": order_id,
        "strategy": "SIMPLE",
        "reason": (
            "No fleet-wide optimisation is required."
        ),
    }

async def plan_routes():

    world = world_manager.get_world()

    route_plan = await routing_service.plan_routes(world)

    if route_plan is None:
        return {
            "status": "NO_ROUTE",
            "routes": [],
        }

    return {
        "status": "SUCCESS",
        "routes": [
            {
                "route_id": route.route_id,
                "vehicle_id": route.vehicle_id,
                "distance": route.total_distance,
                "travel_time": route.total_travel_time,

                "stops": [
                    {
                        "sequence": stop.sequence,
                        "lat": stop.location.lat,
                        "lon": stop.location.lon,
                        "kind": stop.location.kind,
                        "order_id": stop.location.order_id,
                    }
                    for stop in route.stops
                ],

                "segments": [
                    {
                        "nodes": segment.nodes,
                        "geometry": segment.geometry,
                        "distance": segment.distance,
                        "travel_time": segment.travel_time,
                        "instructions": segment.instructions,
                    }
                    for segment in route.segments
                ],
            }
            for route in route_plan.routes
        ],
    }
async def simple_fleet_route(order_id: str):
    compatibility_service = CompatibilityService()
    world = world_manager.get_world()

    # ---------------------------------------------------------
    # Find order
    # ---------------------------------------------------------

    order = next(
        (
            o for o in world.new_orders
            if o.order_id == order_id
        ),
        None,
    )

    if order is None:
        return {
            "success": False,
            "order_id": order_id,
            "error": f"Order {order_id} not found.",
        }

    # ---------------------------------------------------------
    # Evaluate compatibility
    # ---------------------------------------------------------


    compatibility = await compatibility_service.evaluate(
        world,
        order_id,
    )

    print("[COMPATIBILITY]", compatibility)

    if compatibility.status == CompatibilityStatus.UNSERVICEABLE:
        return {
            "success": False,
            "order_id": order_id,
            "status": "UNSERVICEABLE",
            "error": "No compatible vehicle available.",
        }

    if compatibility.status == CompatibilityStatus.WAITING:
        return {
            "success": False,
            "order_id": order_id,
            "status": "WAITING",
            "error": "No vehicle is currently available for this order.",
        }

    if compatibility.status != CompatibilityStatus.ROUTABLE:
        return {
            "success": False,
            "order_id": order_id,
            "status": compatibility.status.value,
            "error": "Order is not currently routable.",
        }

    # ---------------------------------------------------------
    # Select recommended compatible vehicle
    # ---------------------------------------------------------

    if not compatibility.compatible:
        return {
            "success": False,
            "order_id": order_id,
            "status": "UNSERVICEABLE",
            "error": "Compatibility evaluation found no compatible vehicles.",
        }

    recommended = compatibility.compatible[0]

    vehicle_id = recommended.vehicle_id

    if not vehicle_id:
        return {
            "success": False,
            "order_id": order_id,
            "status": "UNSERVICEABLE",
            "error": "Compatibility evaluation did not select a vehicle.",
        }

    # ---------------------------------------------------------
    # Find vehicle
    # ---------------------------------------------------------

    vehicle = next(
        (
            v for v in world.vehicles
            if v.vehicle_id == vehicle_id
        ),
        None,
    )

    if vehicle is None:
        return {
            "success": False,
            "order_id": order_id,
            "status": "UNSERVICEABLE",
            "error": f"Recommended vehicle {vehicle_id} was not found.",
        }

    # ---------------------------------------------------------
    # Build routing locations
    # ---------------------------------------------------------

    if (
        order.pickup_lat is None
        or order.pickup_lon is None
        or order.delivery_lat is None
        or order.delivery_lon is None
    ):
        return {
            "success": False,
            "order_id": order_id,
            "vehicle_id": vehicle_id,
            "error": "Order locations have not been geocoded.",
        }

    # ---------------------------------------------------------
    # Build routing locations
    # ---------------------------------------------------------

    origin = RoutingLocation(
        matrix_index=0,
        graph_node=vehicle.current_node,
        lat=vehicle.current_lat,
        lon=vehicle.current_lon,
        kind="vehicle",
    )

    pickup = RoutingLocation(
        matrix_index=1,
        graph_node=order.pickup_node,
        lat=order.pickup_lat,
        lon=order.pickup_lon,
        kind="pickup",
        order_id=order.order_id,
    )

    delivery = RoutingLocation(
        matrix_index=2,
        graph_node=order.delivery_node,
        lat=order.delivery_lat,
        lon=order.delivery_lon,
        kind="delivery",
        order_id=order.order_id,
    )

    # ---------------------------------------------------------
    # Extract routing constraints
    # ---------------------------------------------------------

    avoid_roads = []
    avoid_areas = []
    required_waypoints = []

    for constraint in order.constraints or []:

        constraint_type = constraint.type
        value = constraint.value

        if constraint_type == "avoid_road":
            avoid_roads.append(value)

        elif constraint_type == "avoid_area":
            avoid_areas.append(value)

        elif constraint_type == "required_waypoint":
            required_waypoints.append(value)

    # ---------------------------------------------------------
    # Route:
    #
    #   vehicle current position
    #           ↓
    #        pickup
    #           ↓
    #       delivery
    #
    # ---------------------------------------------------------

    legs = [
        (origin, pickup),
        (pickup, delivery),
        (delivery, origin),
    ]

    segments = []

    total_distance = 0.0
    total_travel_time = 0.0

    for leg_origin, leg_destination in legs:

        result = simple_routing_tool.route_locations(
            world=world,
            origin=leg_origin,
            destination=leg_destination,
            avoid_roads=avoid_roads,
            avoid_areas=avoid_areas,
            required_waypoints=required_waypoints,
        )

        if not result["success"]:
            return {
                "success": False,
                "order_id": order_id,
                "vehicle_id": vehicle_id,
                "status": "UNROUTABLE",
                "error": result.get("error"),
            }

        route_data = result["route"]

        segment = RouteSegment(
            nodes=route_data["nodes"],
            geometry=route_data["geometry"],
            distance=route_data["distance_m"],
            travel_time=route_data["travel_time_s"],
            instructions=[],
        )

        segments.append(segment)

        total_distance += route_data["distance_m"]
        total_travel_time += route_data["travel_time_s"]
    # ---------------------------------------------------------
    # Build RouteSegment
    # ---------------------------------------------------------

    # ---------------------------------------------------------
    # Build RouteStops
    # ---------------------------------------------------------

    stops = [
        RouteStop(
            sequence=0,
            location=origin,
        ),
        RouteStop(
            sequence=1,
            location=pickup,
        ),
        RouteStop(
            sequence=2,
            location=delivery,
        ),
        RouteStop(
            sequence=3,
            location=origin,
        ),
    ]

    # ---------------------------------------------------------
    # Build VehicleRoute
    # ---------------------------------------------------------

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
    # Commit operational state
    # ---------------------------------------------------------

    order.assigned_vehicle = vehicle.vehicle_id

    vehicle.current_route_id = route_id
    vehicle.current_route = vehicle_route
    vehicle.status = VehicleStatus.EN_ROUTE

    print(
        "[ROUTE COMMIT]",
        {
            "vehicle_id": vehicle.vehicle_id,
            "route_id": route_id,
            "vehicle_current_route_id": vehicle.current_route_id,
            "vehicle_current_route": (
                vehicle.current_route.route_id
                if vehicle.current_route
                else None
            ),
            "status": vehicle.status,
        },
    )

    world.routes.append(vehicle_route)

    if order in world.new_orders:
        world.new_orders.remove(order)

    if order not in world.orders_in_progress:
        world.orders_in_progress.append(order)

    print(
        "[ROUTING WORLD]",
        id(world),
        id(vehicle),
    )


    # ---------------------------------------------------------
    # Return
    # ---------------------------------------------------------

    return {
        "success": True,
        "order_id": order_id,
        "vehicle_id": vehicle.vehicle_id,
        "route_id": route_id,
        "distance_m": total_distance,
        "travel_time_s": total_travel_time,
        "status": "ROUTED",
        "routing_mode": "SIMPLE",
        "avoid_roads": avoid_roads,
        "avoid_areas": avoid_areas,
    }

