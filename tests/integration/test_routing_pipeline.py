import networkx as nx

from models.world_state import WorldState
from models.vehicles.vehicle import VehicleStatus

from routing.matrix_service import MatrixService
from routing.or_tools_solver import ORToolsSolver
from routing.route_builder import RouteBuilder
from services.problem_builder import RoutingProblemBuilder


# ---------------------------------------------------------
# Dummy models
# ---------------------------------------------------------

class DummyDepot:
    graph_node = 0
    lat = 1.300
    lon = 103.800


class DummyVehicle:

    def __init__(self):
        self.vehicle_id = "truck-1"
        self.status = VehicleStatus.IDLE

        self.max_weight_kg = 100
        self.current_node = 0


class DummyOrder:

    def __init__(
            self,
            order_id,
            pickup_node,
            delivery_node,
            weight,
    ):
        self.order_id = order_id

        self.pickup_node = pickup_node
        self.delivery_node = delivery_node

        self.pickup_lat = 1.301
        self.pickup_lon = 103.801

        self.delivery_lat = 1.302
        self.delivery_lon = 103.802

        self.weight_kg = weight


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
        (1, 2, 400),
        (2, 3, 300),
        (3, 4, 200),
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
        vehicles=[DummyVehicle()],
        orders=[
            DummyOrder(
                "order-1",
                pickup_node=1,
                delivery_node=2,
                weight=20,
            ),
            DummyOrder(
                "order-2",
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

    kinds = {
        stop.location.kind
        for stop in vehicle_route.stops
    }

    assert "pickup" in kinds
    assert "delivery" in kinds

    assert len(vehicle_route.segments) > 0

    assert vehicle_route.total_distance >= 0
    assert vehicle_route.total_travel_time >= 0

    assert route_plan.total_distance >= 0
    assert route_plan.total_travel_time >= 0