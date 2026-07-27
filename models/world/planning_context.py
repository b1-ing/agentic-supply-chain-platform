from dataclasses import dataclass


@dataclass
class PlanningContext:
    #
    # Changes since last optimisation
    #

    new_orders: int

    cancelled_orders: int

    vehicle_failures: int

    traffic_incidents: int

    road_closures: int

    #
    # Current state
    #

    vehicles: int

    active_routes: int

    orders_in_progress: int

    idle_vehicles: int
