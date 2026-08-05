from models.routing.route_plan import RoutePlan
from services.routing.matrix_service import MatrixService
from services.routing.problem_builder import RoutingProblemBuilder
from services.routing.route_builder import RouteBuilder
from routing.or_tools_solver import ORToolsSolver


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

    def plan_routes(
            self,
            world,
    ) -> RoutePlan:

        problem = self.problem_builder.build(
            world,
        )

        matrix = self.matrix_service.build(
            world,
            problem.locations,
        )

        print(problem.pickup_delivery_pairs)

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