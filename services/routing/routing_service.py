from __future__ import annotations

from models.routing.route_plan import RoutePlan
from models.routing.compatibility_result import (
    CompatibilityResult,
    CompatibilityStatus,
)
from models.routing.compatible_vehicle import CompatibleVehicle
from models.routing.incompatible_vehicle import IncompatibleVehicle

from services.routing.matrix_service import MatrixService
from services.routing.problem_builder import RoutingProblemBuilder
from services.routing.route_builder import RouteBuilder
from services.routing.compatibility_service import CompatibilityService

from routing.or_tools_solver import ORToolsSolver


class RoutingService:
    """
    High-level fleet routing service.

    Responsibilities
    ----------------
    - Evaluate vehicle compatibility for new orders.
    - Store compatibility results in WorldState.
    - Build the fleet-wide routing problem.
    - Build the travel-time matrix.
    - Solve the pickup/delivery CVRP using OR-Tools.
    - Convert the solution into a RoutePlan.
    - Commit successful routes/orders to WorldState.

    This is the fleet-wide equivalent of simple_fleet_route().
    """

    def __init__(self):

        #inits all the services needed
        self.compatibility_service = CompatibilityService()
        self.problem_builder = RoutingProblemBuilder()
        self.matrix_service = MatrixService()
        self.solver = ORToolsSolver()
        self.route_builder = RouteBuilder()

    # ================================================================
    # PUBLIC API
    # ================================================================
    async def plan_routes(
        self,
        world,
    ) -> RoutePlan:

        for order in list(world.new_orders):

            # ---------------------------------------------------------
            # safety net to check if the order has been geocoded and snapped to graph
            # ---------------------------------------------------------

            if (
                order.pickup_node is None
                or order.delivery_node is None
            ):
                print(
                    f"Skipping order {order.order_id}: "
                    "pickup or delivery has not been resolved."
                )
                continue

            compatibility = await self.compatibility_service.evaluate(
                world,
                order.order_id,
            )

            # Store the typed compatibility result
            world.compatibility_results[order.order_id] = compatibility

            # ---------------------------------------------------------
            # UNSERVICEABLE
            # ---------------------------------------------------------

            if compatibility.status == CompatibilityStatus.UNSERVICEABLE:
                world.new_orders.remove(order)
                world.unserviceable_orders.append(order)

                return {
                    "success": False,
                    "order_id": order.order_id,
                    "status": "UNSERVICEABLE",
                    "error": "No compatible vehicle available.",
                }

            # ---------------------------------------------------------
            # WAITING
            # ---------------------------------------------------------

            if compatibility.status == CompatibilityStatus.WAITING:
                continue

            # ---------------------------------------------------------
            # ROUTABLE
            # ---------------------------------------------------------

            if compatibility.status != CompatibilityStatus.ROUTABLE:
                continue

        # -------------------------------------------------------------
        # Build CVRP problem
        # -------------------------------------------------------------

        problem = self.problem_builder.build(
            world,
        )

        # -------------------------------------------------------------
        # Build travel matrix
        # -------------------------------------------------------------

        matrix = self.matrix_service.build(
            world.graph,
            world,
            problem.locations,
        )

        # -------------------------------------------------------------
        # Solve CVRP
        # -------------------------------------------------------------

        print("\n=== CVRP INPUT ===")

        for i, location in enumerate(problem.locations):
            print(
                i,
                location.kind,
                location.order_id,
                "node=",
                location.graph_node,
            )

        print("\n=== PICKUP/DELIVERY PAIRS ===")

        for pair in problem.pickup_delivery_pairs:
            print(pair)

        routes = self.solver.solve(
            matrix=matrix.matrix,
            starts=problem.starts,
            ends=problem.ends,
            demands=problem.demands,
            capacities=problem.capacities,
            pickup_delivery_pairs=problem.pickup_delivery_pairs,
        )

        if routes is None:
            raise RuntimeError(
                "No feasible routing solution found."
            )

        # -------------------------------------------------------------
        # Build domain RoutePlan
        # -------------------------------------------------------------

        route_plan = self.route_builder.build(
            world=world,
            routes=routes,
            travel_matrix=matrix,
            vehicles=problem.vehicles,
        )

        self._commit_route_plan(
            world,
            route_plan,
        )

        return route_plan


    # ================================================================
    # WORLD STATE COMMIT
    # ================================================================

    @staticmethod
    def _commit_route_plan(
        world,
        route_plan: RoutePlan,
    ) -> None:
        """
        Commit a successfully generated RoutePlan.

        RouteBuilder is responsible for attaching the generated
        VehicleRoute to the vehicle.

        This method handles order lifecycle and WorldState.routes.
        """

        routed_order_ids = set()

        for vehicle_route in route_plan.routes:

            for stop in vehicle_route.stops:

                location = stop.location

                if (
                    location.order_id is not None
                    and location.kind in (
                        "pickup",
                        "delivery",
                    )
                ):
                    routed_order_ids.add(
                        location.order_id
                    )

        # ------------------------------------------------------------
        # Move successfully routed orders
        # ------------------------------------------------------------

        for order in list(world.new_orders):

            if order.order_id not in routed_order_ids:
                continue

            world.new_orders.remove(order)

            if order not in world.orders_in_progress:
                world.orders_in_progress.append(
                    order
                )

            # The route now owns this assignment.
            # Vehicle assignment is handled below through the
            # generated VehicleRoute.

        # ------------------------------------------------------------
        # Assign orders to their actual vehicle
        # ------------------------------------------------------------

        for vehicle_route in route_plan.routes:

            for stop in vehicle_route.stops:

                location = stop.location

                if location.order_id is None:
                    continue

                order = next(
                    (
                        candidate
                        for candidate in world.orders_in_progress
                        if candidate.order_id
                        == location.order_id
                    ),
                    None,
                )

                if order is not None:
                    order.assigned_vehicle = (
                        vehicle_route.vehicle_id
                    )

        # ------------------------------------------------------------
        # Add routes to WorldState exactly once
        # ------------------------------------------------------------

        existing_route_ids = {
            route.route_id
            for route in world.routes
        }

        for vehicle_route in route_plan.routes:

            if vehicle_route.route_id not in existing_route_ids:
                world.routes.append(
                    vehicle_route
                )