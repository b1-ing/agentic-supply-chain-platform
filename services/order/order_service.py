# services/order/order_service.py

from graphs.order.order_graph import build_order_graph
from models.order.order_state import OrderState
from services.world.world_manager import world_manager

from agents.planning.planning_decision_agent import PlanningDecisionAgent
from services.routing.routing_service import RoutingService
from models.vehicles.vehicle import VehicleStatus


class OrderService:
    def __init__(self):
        self.order_graph = build_order_graph()
        self.planner = PlanningDecisionAgent()
        self.routing = RoutingService()

    async def process_order(
        self,
        prompt: str,
    ):
        """
        Process a user order through the complete order pipeline.

        Flow:

            Prompt
              ↓
            Order Graph
              ↓
            WorldState
              ↓
            Planning Agent
              ↓
            Routing Agent
              ↓
            WorldState
        """

        world = world_manager.get_world()

        ############################################################
        # 1. Extract order
        ############################################################

        state = OrderState(
            raw_order=prompt,
            world=world,
        )

        self.order_graph.invoke(
            state,
            config={
                "run_name": "Order Graph",
                "configurable": {
                    "thread_id": "order",
                },
            },
        )

        # Find the order that was actually created.
        if not world.orders_in_progress:
            return {
                "success": False,
                "error": "Order was not created.",
            }

        order = world.orders_in_progress[-1]

        return {
            "success": True,
            "order_id": order.order_id,
            "order": order,
        }

    ################################################################
    # Commit routing results
    ################################################################

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
            vehicle = next(
                (v for v in world.vehicles if v.vehicle_id == new_route.vehicle_id),
                None,
            )

            if vehicle is None:
                continue

            #
            # Update vehicle status
            #

            if len(new_route.stops) > 0:
                vehicle.status = VehicleStatus.EN_ROUTE
            else:
                vehicle.status = VehicleStatus.IDLE

            #
            # Find existing route
            #

            existing = next(
                (r for r in world.routes if r.vehicle_id == new_route.vehicle_id),
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
            # Move assigned orders
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
        # Move routed orders out of new_orders
        ############################################################

        new_order_ids = []
        for order in routed_orders:
            if order in world.new_orders:
                world.new_orders.remove(order)
                new_order_ids.append(order.order_id)

            if order not in world.orders_in_progress:
                world.orders_in_progress.append(order)

        return new_order_ids


