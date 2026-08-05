from agents.planning.planning_decision_agent import PlanningDecisionAgent

from services.planning_context_builder import PlanningContextBuilder
from services.traffic_penalty_service import TrafficPenaltyService

from services.order.geocoding_service import GeocodingService
from services.graph_snap_service import GraphSnapService
# from services.compatibility_service import CompatibilityService

from routing.problem_builder import RoutingProblemBuilder
from services.routing.matrix_service import MatrixService

from routing.or_tools_solver import ORToolsSolver
from routing.route_builder import RouteBuilder
from routing.valhalla_routing_service import ValhallaRoutingService

from services.world_updater import WorldUpdater


class PlanningAgent:
    """
    Main orchestration agent.

    Responsibilities
    ----------------
    1. Build planning context.
    2. Ask the LLM whether replanning is required.
    3. Update graph with traffic penalties.
    4. Process any new orders.
    5. Build routing problem.
    6. Optimise with OR-Tools.
    7. Convert optimisation output into vehicle routes.
    8. Generate navigable road routes using Valhalla.
    9. Update the WorldState.
    """

    def __init__(self):

        #
        # LLM
        #

        self.decision_agent = PlanningDecisionAgent()

        #
        # Context
        #

        self.context_builder = PlanningContextBuilder()

        #
        # Graph / traffic
        #

        self.penalty_service = TrafficPenaltyService()

        #
        # Order processing
        #

        self.geocoder = GeocodingService()
        self.snapper = GraphSnapService()
        self.compatibility_service = CompatibilityService()

        #
        # Optimisation
        #

        self.problem_builder = RoutingProblemBuilder()
        self.matrix_service = MatrixService()
        self.solver = ORToolsSolver()

        #
        # Route construction
        #

        self.route_builder = RouteBuilder()
        self.routing_service = ValhallaRoutingService()

        #
        # Persist changes
        #

        self.world_updater = WorldUpdater()

    async def run(
        self,
        world,
    ):
        """
        Execute one planning cycle.

        Returns
        -------
        RoutePlan | None
        """

        ####################################################################
        # 1. Build planning context
        ####################################################################

        context = self.context_builder.build(
            world,
        )

        ####################################################################
        # 2. Ask the Planning Decision Agent
        ####################################################################

        decision = await self.decision_agent.run(
            world,
            context,
        )

        world.summary = decision.summary

        ####################################################################
        # 3. No optimisation required
        ####################################################################

        if not decision.should_replan:
            world.recommend_replan = False

            return None

        world.recommend_replan = True

        ####################################################################
        # 4. Apply traffic penalties
        ####################################################################

        self.penalty_service.apply(
            world=world,
            decision=decision,
        )

        ####################################################################
        # 5. Process newly arrived orders
        ####################################################################

        compatible_orders = []

        for order in world.new_orders:
            #
            # Geocode
            #

            if order.pickup_node is None:
                pickup = self.geocoder.geocode(
                    order.pickup_address,
                )

                if pickup is None:
                    continue

                order.pickup_lat, order.pickup_lon = pickup

            if order.delivery_node is None:
                delivery = self.geocoder.geocode(
                    order.delivery_address,
                )

                if delivery is None:
                    continue

                order.delivery_lat, order.delivery_lon = delivery

            #
            # Snap onto graph
            #

            if order.pickup_node is None:
                order.pickup_node = self.snapper.snap(
                    world.graph,
                    order.pickup_lat,
                    order.pickup_lon,
                )

            if order.delivery_node is None:
                order.delivery_node = self.snapper.snap(
                    world.graph,
                    order.delivery_lat,
                    order.delivery_lon,
                )

            compatible_orders.append(order)

        ####################################################################
        # 6. Determine compatible vehicles
        ####################################################################

        #         compatible_orders = self.compatibility_service.filter(
        #             world.vehicles,
        #             compatible_orders,
        #         )

        ####################################################################
        # Nothing can be routed
        ####################################################################

        if not compatible_orders:
            return None

        ####################################################################
        # 7. Build routing problem
        ####################################################################

        problem = self.problem_builder.build(
            world,
        )

        if len(problem.locations) == 0:
            return None

        if len(problem.vehicles) == 0:
            return None

        ####################################################################
        # 8. Travel matrix
        ####################################################################

        travel_matrix = self.matrix_service.build(
            world,
            problem.locations,
        )

        ####################################################################
        # 9. Optimise
        ####################################################################

        routes = self.solver.solve(
            matrix=travel_matrix.matrix,
            starts=problem.starts,
            ends=problem.ends,
            demands=problem.demands,
            capacities=problem.capacities,
            pickup_delivery_pairs=problem.pickup_delivery_pairs,
        )

        if routes is None:
            return None

        ####################################################################
        # 10. Build logical routes
        ####################################################################

        route_plan = self.route_builder.build(
            world=world,
            routes=routes,
            travel_matrix=travel_matrix,
            vehicles=problem.vehicles,
        )

        ####################################################################
        # 11. Generate navigable routes
        ####################################################################

        route_plan = self.routing_service.build(
            route_plan,
        )

        ####################################################################
        # 12. Persist everything
        ####################################################################

        self.world_updater.update(
            world=world,
            decision=decision,
            route_plan=route_plan,
        )

        ####################################################################
        # Finished
        ####################################################################

        return route_plan
