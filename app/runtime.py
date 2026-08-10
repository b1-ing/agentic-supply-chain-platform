import time

from app.initialise import initialise_world
import asyncio
from graphs.order.order_graph import build_order_graph

from agents.planning.planning_decision_agent import PlanningDecisionAgent

from services.routing.routing_service import RoutingService
from services.routing.route_visualiser import RouteVisualiser
from services.traffic.traffic_pipeline import TrafficPipeline
from services.world.world_manager import world_manager
from models.vehicles.vehicle import VehicleStatus
from models.order.order_state import OrderState


class Runtime:

    def __init__(self):

        initialise_world()

        self.order_graph = build_order_graph()

        self.traffic_pipeline = TrafficPipeline()

        self.planner = PlanningDecisionAgent()

        self.routing = RoutingService()

    ####################################################################
    # Main loop
    ####################################################################

    async def run(self):

        while True:

            prompt = input("> ").strip()

            #
            # Nothing entered
            #

            if not prompt:
                continue

            ############################################################
            # Extract order
            ############################################################

            world = world_manager.get_world()

            state = OrderState(
                raw_order=prompt,
                world=world,
            )

            state = self.order_graph.invoke(
                state,
                config={
                    "run_name": "Order Graph",
                    "configurable": {
                        "thread_id": "order",
                    },
                },
            )

            ############################################################
            # Update traffic
            ############################################################

            # self.traffic_pipeline.update()

            ############################################################
            # Planning agent
            ############################################################

            decision = await self.planner.run(world)

            print(decision)

            ############################################################
            # Routing
            ############################################################
            if decision.should_replan:
                route_plan = self.routing.plan_routes(world)

                for route in route_plan.routes:
                    print(f"\n{route.vehicle_id}")

                    for stop in route.stops:
                        print(
                            stop.location.kind,
                            stop.location.order_id,
                            stop.location.matrix_index,
                        )

                self._commit_routes(
                    world,
                    route_plan,
                )

                ############################################################
                # Visualise
                ############################################################

                RouteVisualiser().save(
                    world,
                    output_file="output/live_map.html",
                )

                print(
                    f"\nPending orders      : {len(world.new_orders)}"
                )

                print(
                    f"In-progress orders  : {len(world.orders_in_progress)}"
                )

                print(
                    f"Vehicle routes      : {len(world.routes)}"
                )

                print(
                    "Map updated -> output/live_map.html\n"
                )

                time.sleep(1)

    ####################################################################
    # Commit routing results
    ####################################################################

    def _commit_routes(
            self,
            world,
            route_plan,
    ):

        routed_orders = []

        ############################################################
        # Update fleet routes
        ############################################################

        for new_route in route_plan.routes:

            #
            # Replace existing vehicle route
            #
            for new_route in route_plan.routes:

                vehicle = next(
                    v for v in world.vehicles
                    if v.vehicle_id == new_route.vehicle_id
                )

                if len(new_route.stops) > 0:
                    vehicle.status = VehicleStatus.EN_ROUTE
                else:
                    vehicle.status = VehicleStatus.IDLE

            existing = next(
                (
                    r
                    for r in world.routes
                    if r.vehicle_id == new_route.vehicle_id
                ),
                None,
            )

            if existing is None:

                world.routes.append(new_route)

            else:

                existing.stops = new_route.stops
                existing.segments = new_route.segments
                existing.total_distance = new_route.total_distance
                existing.total_travel_time = new_route.total_travel_time

            ########################################################
            # Move assigned orders into orders_in_progress
            ########################################################

            for stop in new_route.stops:

                if stop.location.kind != "pickup":
                    continue

                order = next(
                    (
                        o
                        for o in world.new_orders
                        if o.order_id == stop.location.order_id
                    ),
                    None,
                )

                if order is None:
                    continue

                order.assigned_vehicle = new_route.vehicle_id

                routed_orders.append(order)

        ############################################################
        # Remove from pending
        ############################################################

        for order in routed_orders:

            if order in world.new_orders:
                world.new_orders.remove(order)

            if order not in world.orders_in_progress:
                world.orders_in_progress.append(order)