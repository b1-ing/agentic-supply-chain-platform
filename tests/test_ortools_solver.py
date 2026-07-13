import numpy as np

from models.routing_location import RoutingLocation
from models.travel_matrix import TravelMatrix
from routing.or_tools_solver import ORToolsSolver


# ---------------------------------------------------------
# Dummy models
# ---------------------------------------------------------


class DummyVehicle:
    def __init__(self, vehicle_id, capacity):

        self.id = vehicle_id
        self.max_weight = capacity

        self.route = []


class DummyOrder:
    def __init__(self, order_id, weight):

        self.id = order_id
        self.weight_kg = weight


# ---------------------------------------------------------
# Test
# ---------------------------------------------------------


def test_solver():

    #
    # Matrix indices
    #
    # 0 Depot
    # 1 Order A
    # 2 Order B
    # 3 Order C
    #

    locations = [
        RoutingLocation(
            id="Depot",
            graph_node=0,
            location_type="depot",
        ),
        RoutingLocation(
            id="OrderA",
            graph_node=1,
            location_type="delivery",
        ),
        RoutingLocation(
            id="OrderB",
            graph_node=2,
            location_type="delivery",
        ),
        RoutingLocation(
            id="OrderC",
            graph_node=3,
            location_type="delivery",
        ),
    ]

    matrix = np.array(
        [
            [0, 5, 7, 8],
            [5, 0, 2, 4],
            [7, 2, 0, 3],
            [8, 4, 3, 0],
        ]
    )

    travel_matrix = TravelMatrix(
        matrix=matrix,
        locations=locations,
    )

    vehicles = [
        DummyVehicle(
            "Truck-1",
            100,
        ),
        DummyVehicle(
            "Truck-2",
            100,
        ),
    ]

    orders = [
        DummyOrder(
            "OrderA",
            20,
        ),
        DummyOrder(
            "OrderB",
            30,
        ),
        DummyOrder(
            "OrderC",
            10,
        ),
    ]

    solver = ORToolsSolver()

    solver.solve(
        world=None,
        travel_matrix=travel_matrix,
        vehicles=vehicles,
        orders=orders,
    )

    print()

    print("=" * 50)

    print("Routes")

    print("=" * 50)

    for vehicle in vehicles:
        print(vehicle.id)

        for stop in vehicle.route:
            print("   ", stop)

        print()

    #
    # Basic correctness checks
    #

    all_orders = []

    for vehicle in vehicles:
        all_orders.extend(vehicle.route)

    assert len(all_orders) == len(orders)

    assert len(set(all_orders)) == len(orders)
