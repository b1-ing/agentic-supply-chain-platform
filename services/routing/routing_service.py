from models.routing.route_plan import RoutePlan
from services.routing.matrix_service import MatrixService

from services.routing.problem_builder import RoutingProblemBuilder
from services.routing.route_builder import RouteBuilder
from routing.or_tools_solver import ORToolsSolver
from services.routing.compatibility_service import CompatibilityService
from models.routing.compatibility_result import CompatibilityStatus


class RoutingService:
    """
    High-level fleet routing service.

    Responsibilities
    ----------------
    - Build routing problem
    - Build travel matrix
    - Invoke ORTools
    - Convert solution into RoutePlan
    """

    def __init__(self):

        self.problem_builder = RoutingProblemBuilder()
        self.matrix_service = MatrixService()
        self.solver = ORToolsSolver()
        self.route_builder = RouteBuilder()
        self.compatibility_service = CompatibilityService()

    async def plan_routes(
        self,
        world,
    ) -> RoutePlan:

        for order in list(world.new_orders):

            compatibility = await self.compatibility_service.evaluate(
                order.order_id
            )

            if compatibility["status"] == "UNSERVICEABLE":
                    return {
                        "success": False,
                        "order_id": order.order_id,
                        "status": "UNSERVICEABLE",
                        "error": "No compatible vehicle available.",
                    }

            vehicle_id = compatibility.get("recommended_vehicle_id")

            if not vehicle_id:
                return {
                    "success": False,
                    "order_id": order.order_id,
                    "status": "UNSERVICEABLE",
                    "error": "Compatibility evaluation did not select a vehicle.",
                }
            world.new_orders.remove(order)
            world.unserviceable_orders.append(order)

        problem = self.problem_builder.build(
            world,
        )

        matrix = self.matrix_service.build(
            world,
            problem.locations,
        )


        routes = self.solver.solve(
            matrix=matrix.matrix,
            starts=problem.starts,
            ends=problem.ends,
            demands=problem.demands,
            capacities=problem.capacities,
            pickup_delivery_pairs=problem.pickup_delivery_pairs,
        )

        if routes is None:
            raise RuntimeError("No feasible routing solution found.")

        return self.route_builder.build(
            world=world,
            routes=routes,
            travel_matrix=matrix,
            vehicles=problem.vehicles,
        )
