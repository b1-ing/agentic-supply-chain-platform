import networkx as nx

from models.world_state import WorldState
from models.vehicles.vehicle import VehicleStatus
from models.vehicles.standard_truck import StandardTruck

from routing.matrix_service import MatrixService
from routing.or_tools_solver import ORToolsSolver
from routing.route_builder import RouteBuilder
from services.problem_builder import RoutingProblemBuilder
from models.order import Order
from models.incoming_state import IncomingOrder

# ---------------------------------------------------------
# Dummy models
# ---------------------------------------------------------


class DummyDepot:
    graph_node = 0
    lat = 1.300
    lon = 103.800


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------


def build_test_graph() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    coordinates = {
        0: (103.800, 1.300),
        1: (103.801, 1.301),
        2: (103.802, 1.302),
        3: (103.803, 1.303),
        4: (103.804, 1.304),
    }

    for node, (lon, lat) in coordinates.items():
        graph.add_node(
            node,
            x=lon,
            y=lat,
        )

    edges = [
        (0, 1, 500),
        (1, 0, 500),
        (1, 2, 400),
        (2, 1, 400),
        (2, 3, 300),
        (3, 2, 300),
        (3, 4, 200),
        (4, 3, 200),
        (4, 0, 600),
        (0, 4, 600),
    ]

    for u, v, length in edges:
        graph.add_edge(
            u,
            v,
            travel_time=5,
            length=length,
        )

    return graph


# ---------------------------------------------------------
# Integration test
# ---------------------------------------------------------


def test_full_routing_pipeline():

    # --------------------------------------------------
    # Arrange
    # --------------------------------------------------

    world = WorldState(
        graph=build_test_graph(),
        depots=[DummyDepot()],
        vehicles=[StandardTruck(vehicle_id="1")],
        orders=[
            IncomingOrder(
                pickup_address="location A",
                delivery_address=" ",
                order_id="order-1",
                pickup_node=1,
                delivery_node=3,
                weight=20,
            ),
            IncomingOrder(
                pickup_address="location B",
                delivery_address=" ",
                order_id="order-2",
                pickup_node=2,
                delivery_node=4,
                weight=30,
            ),
        ],
    )

    problem = RoutingProblemBuilder().build(world)

    # Insert this right after building the problem in your test
    #     print("\n--- DEBUG: Location Indices ---")
    #     for loc in problem.locations:
    #         print(f"Index: {loc.matrix_index} | Kind: {loc.kind:<8} | Graph Node: {loc.graph_node} | ID: {getattr(loc, 'order_id', 'N/A')}")
    #
    #     print(f"Vehicle Starts Matrix Indices: {problem.starts}")
    #     print(f"Vehicle Ends Matrix Indices:   {problem.ends}")
    #     print("-------------------------------\n")
    #
    matrix = MatrixService().build(
        world,
        problem.locations,
    )

    #     print(matrix.matrix)

    # --------------------------------------------------
    # Act
    # --------------------------------------------------

    routes = ORToolsSolver().solve(
        matrix=matrix.matrix,
        starts=problem.starts,
        ends=problem.ends,
        demands=problem.demands,
        capacities=problem.capacities,
        pickup_delivery_pairs=problem.pickup_delivery_pairs,
    )

    assert routes is not None

    print("routes:", routes)

    route_plan = RouteBuilder().build(
        world=world,
        routes=routes,
        travel_matrix=matrix,
        vehicles=problem.vehicles,
    )

    # --------------------------------------------------
    # Assert
    # --------------------------------------------------

    assert route_plan is not None
    assert len(route_plan.routes) == 1

    vehicle_route = route_plan.routes[0]

    assert vehicle_route.stops
    assert vehicle_route.stops[0].location.kind == "depot"
    assert vehicle_route.stops[-1].location.kind == "depot"

    kinds = {stop.location.kind for stop in vehicle_route.stops}

    assert "pickup" in kinds
    assert "delivery" in kinds

    assert len(vehicle_route.segments) > 0

    assert vehicle_route.total_distance >= 0
    assert vehicle_route.total_travel_time >= 0

    assert route_plan.total_distance >= 0
    assert route_plan.total_travel_time >= 0


def test_multiple_vehicles():

    world = WorldState(
        graph=build_test_graph(),
        depots=[DummyDepot()],
        vehicles=[
            StandardTruck(vehicle_id="truck-1"),
            StandardTruck(vehicle_id="truck-2"),
        ],
        orders=[
            IncomingOrder(
                order_id="order-1",
                pickup_address="A",
                delivery_address="B",
                pickup_node=1,
                delivery_node=2,
                weight=20,
            ),
            IncomingOrder(
                order_id="order-2",
                pickup_address="C",
                delivery_address="D",
                pickup_node=3,
                delivery_node=4,
                weight=30,
            ),
        ],
    )

    problem = RoutingProblemBuilder().build(world)

    matrix = MatrixService().build(
        world,
        problem.locations,
    )

    routes = ORToolsSolver().solve(
        matrix=matrix.matrix,
        starts=problem.starts,
        ends=problem.ends,
        demands=problem.demands,
        capacities=problem.capacities,
        pickup_delivery_pairs=problem.pickup_delivery_pairs,
    )

    assert routes is not None
    assert len(routes) == 2

    route_plan = RouteBuilder().build(
        world=world,
        routes=routes,
        travel_matrix=matrix,
        vehicles=problem.vehicles,
    )

    assert len(route_plan.routes) == 2

    #
    # Every route starts/ends at depot
    #
    for route in route_plan.routes:
        assert route.stops[0].location.kind == "depot"
        assert route.stops[-1].location.kind == "depot"

    #
    # Every pickup/delivery appears exactly once
    #
    visited = []

    for route in route_plan.routes:
        for stop in route.stops:
            if stop.location.kind != "depot":
                visited.append(
                    (
                        stop.location.order_id,
                        stop.location.kind,
                    )
                )

    assert len(visited) == 4
    assert len(set(visited)) == 4


def test_pickups_occur_before_deliveries():

    world = WorldState(
        graph=build_test_graph(),
        depots=[DummyDepot()],
        vehicles=[
            StandardTruck(vehicle_id="truck-1"),
        ],
        orders=[
            IncomingOrder(
                order_id="order-1",
                pickup_address="A",
                delivery_address="B",
                pickup_node=1,
                delivery_node=2,
                weight=20,
            ),
            IncomingOrder(
                order_id="order-2",
                pickup_address="C",
                delivery_address="D",
                pickup_node=3,
                delivery_node=4,
                weight=30,
            ),
        ],
    )

    problem = RoutingProblemBuilder().build(world)

    matrix = MatrixService().build(
        world,
        problem.locations,
    )

    routes = ORToolsSolver().solve(
        matrix=matrix.matrix,
        starts=problem.starts,
        ends=problem.ends,
        demands=problem.demands,
        capacities=problem.capacities,
        pickup_delivery_pairs=problem.pickup_delivery_pairs,
    )

    route_plan = RouteBuilder().build(
        world=world,
        routes=routes,
        travel_matrix=matrix,
        vehicles=problem.vehicles,
    )

    route = route_plan.routes[0]

    for order in world.orders:
        pickup_index = next(
            i
            for i, stop in enumerate(route.stops)
            if stop.location.kind == "pickup"
            and stop.location.order_id == order.order_id
        )

        delivery_index = next(
            i
            for i, stop in enumerate(route.stops)
            if stop.location.kind == "delivery"
            and stop.location.order_id == order.order_id
        )

        assert pickup_index < delivery_index
