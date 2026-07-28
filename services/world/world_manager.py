# services/world/world_manager.py

from threading import Lock

from models.world.world_state import WorldState
from models.order.incoming_order import IncomingOrder
from models.routing.route_plan import RoutePlan
from models.vehicles.vehicle import Vehicle
from models.traffic.traffic_incident import TrafficIncident


class WorldManager:
    """
    Owns the single live WorldState.

    Every component in the system should obtain the world
    through this class.

    Responsibilities
    ----------------
    - Own the singleton WorldState
    - Initialise the world
    - Thread-safe mutations
    - Provide read access

    NOT responsible for:
    - Planning
    - Traffic analysis
    - Routing
    - ORTools
    """

    def __init__(self):

        self._lock = Lock()

        self._world: WorldState | None = None

    ####################################################################
    # Initialisation
    ####################################################################

    def initialise(
        self,
        graph,
        vehicles,
        mapping=None,
    ) -> None:
        """
        Called once during application startup.
        """

        with self._lock:
            self._world = WorldState(
                graph=graph,
                mapping=mapping,
                vehicles=vehicles,
            )

    ####################################################################
    # Access
    ####################################################################

    def get_world(self) -> WorldState:

        if self._world is None:
            raise RuntimeError("WorldManager has not been initialised.")

        return self._world

    ####################################################################
    # Orders
    ####################################################################

    def add_order(
        self,
        order: IncomingOrder,
    ):

        with self._lock:
            self._world.new_orders.append(order)

    def move_order_to_in_progress(
        self,
        order_id: str,
    ):

        with self._lock:
            for order in self._world.new_orders:
                if order.order_id == order_id:
                    self._world.new_orders.remove(order)

                    self._world.orders_in_progress.append(order)

                    return

    def complete_order(
        self,
        order_id: str,
    ):

        with self._lock:
            for order in self._world.orders_in_progress:
                if order.order_id == order_id:
                    self._world.orders_in_progress.remove(order)

                    return

    def cancel_order(
        self,
        order_id: str,
    ):

        with self._lock:
            #
            # Search new orders
            #

            for order in self._world.new_orders:
                if order.order_id == order_id:
                    self._world.new_orders.remove(order)

                    self._world.cancelled_orders.append(order)

                    return

            #
            # Search active orders
            #

            for order in self._world.orders_in_progress:
                if order.order_id == order_id:
                    self._world.orders_in_progress.remove(order)

                    self._world.cancelled_orders.append(order)

                    return

    ####################################################################
    # Vehicles
    ####################################################################

    def update_vehicle(
        self,
        vehicle: Vehicle,
    ):

        with self._lock:
            for i, existing in enumerate(self._world.vehicles):
                if existing.vehicle_id == vehicle.vehicle_id:
                    self._world.vehicles[i] = vehicle

                    return

    ####################################################################
    # Traffic
    ####################################################################

    def replace_traffic_events(
        self,
        incidents: list[TrafficIncident],
    ):

        with self._lock:
            self._world.traffic_events = incidents

    ####################################################################
    # Graph
    ####################################################################

    def update_graph(
        self,
        graph,
    ):

        with self._lock:
            self._world.graph = graph

    ####################################################################
    # Routes
    ####################################################################

    def update_routes(
        self,
        route_plan: RoutePlan,
    ):

        with self._lock:
            self._world.routes = route_plan.routes

    ####################################################################
    # Planning
    ####################################################################

    def update_summary(
        self,
        summary: str,
    ):

        with self._lock:
            self._world.summary = summary

    def set_replan_flag(
        self,
        value: bool,
    ):

        with self._lock:
            self._world.recommend_replan = value

    ####################################################################
    # Reset
    ####################################################################

    def reset(self):

        with self._lock:
            self._world.new_orders.clear()
            self._world.orders_in_progress.clear()
            self._world.cancelled_orders.clear()

            self._world.traffic_events.clear()
            self._world.matched_events.clear()

            self._world.routes.clear()

            self._world.assessments.clear()
            self._world.constraints.clear()

            self._world.summary = ""
            self._world.recommend_replan = False


#
# Singleton
#

world_manager = WorldManager()
