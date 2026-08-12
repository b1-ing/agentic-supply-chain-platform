import networkx as nx

from models.order.incoming_order import IncomingOrder
from models.vehicles.standard_truck import StandardTruck
from models.world.world_state import WorldState

from routing.or_tools_solver import ORToolsSolver

from services.routing.matrix_service import MatrixService
from services.routing.problem_builder import RoutingProblemBuilder
from services.routing.route_builder import RouteBuilder


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
        (0, 1),
        (1, 0),
        (1, 2),
        (2, 1),
        (2, 3),
        (3, 2),
        (3, 4),
        (4, 3),
        (4, 0),
        (0, 4),
    ]

    for u, v in edges:
        graph.add_edge(
            u,
            v,
            travel_time=5,
            length=500,
        )

    return graph


def build_world(num_vehicles=1) -> WorldState:

    vehicles = []

    for i in range(num_vehicles):
        truck = StandardTruck(
            vehicle_id=f"truck-{i}",
        )

        #
        # Update these field names to match your Vehicle model.
        #
        truck.current_node = 0

        vehicles.append(truck)

    orders = [
        IncomingOrder(
            order_id="order-1",
            pickup_address="A",
            delivery_address="B",
            pickup_node=1,
            delivery_node=2,
            weight_kg=20,
        ),
        IncomingOrder(
            order_id="order-2",
            pickup_address="C",
            delivery_address="D",
            pickup_node=3,
            delivery_node=4,
            weight_kg=30,
        ),
    ]

    return WorldState(
        graph=build_test_graph(),
        vehicles=vehicles,
        new_orders=orders,
    )


def solve(world: WorldState):

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

    return problem, matrix, routes, route_plan


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------


def test_full_routing_pipeline():

    world = build_world()

    _, _, routes, route_plan = solve(world)

    assert routes is not None

    assert route_plan is not None
    assert len(route_plan.routes) == 1

    route = route_plan.routes[0]

    assert len(route.stops) > 0
    assert len(route.segments) > 0

    assert route.total_distance >= 0
    assert route.total_travel_time >= 0

    assert route_plan.total_distance >= 0
    assert route_plan.total_travel_time >= 0


def test_multiple_vehicles():

    world = build_world(num_vehicles=2)

    _, _, routes, route_plan = solve(world)

    assert routes is not None
    assert len(route_plan.routes) == 2


def test_pickups_before_deliveries():

    world = build_world()

    _, _, _, route_plan = solve(world)

    route = route_plan.routes[0]

    for order in world.new_orders:
        pickup = next(
            i
            for i, stop in enumerate(route.stops)
            if stop.location.kind == "pickup"
            and stop.location.order_id == order.order_id
        )

        delivery = next(
            i
            for i, stop in enumerate(route.stops)
            if stop.location.kind == "delivery"
            and stop.location.order_id == order.order_id
        )

        assert pickup < delivery
