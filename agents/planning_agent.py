from services.compatibility_service import CompatibilityService
from services.location_builder_service import LocationBuilderService
from services.matrix_service import MatrixService
from services.ortools_solver import ORToolsSolver


class PlanningAgent:
    def __init__(self):

        self.compatibility_service = CompatibilityService()
        self.location_builder = LocationBuilderService()
        self.matrix_service = MatrixService()
        self.solver = ORToolsSolver()

    async def run(self, world):

        #
        # 1. Determine compatible vehicles
        #

        compatible_orders = self.compatibility_service.filter(
            world.fleet,
            world.orders,
        )

        if not compatible_orders:
            return

        #
        # 2. Build routing locations
        #

        locations = self.location_builder.build(
            world.fleet,
            compatible_orders,
        )

        #
        # 3. Build travel matrix
        #

        travel_matrix = self.matrix_service.build(
            world,
            locations,
        )

        #
        # 4. Solve routing problem
        #

        self.solver.solve(
            world=world,
            travel_matrix=travel_matrix,
            vehicles=world.fleet,
            orders=compatible_orders,
        )

        #
        # 5. Vehicles in world.fleet now contain updated routes
        #
