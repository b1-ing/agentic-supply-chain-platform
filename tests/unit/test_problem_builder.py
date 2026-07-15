import pytest
import networkx as nx

from models.routing_problem import RoutingProblem
from models.world_state import WorldState
from models.routing_location import RoutingLocation
from models.vehicles.vehicle import VehicleStatus
from services.problem_builder import RoutingProblemBuilder


# ---------------------------------------------------------------------
# Dummy models for testing
# ---------------------------------------------------------------------

class DummyDepot:
    def __init__(self):
        self.graph_node = 100
        self.lat = 1.3000
        self.lon = 103.8000


class DummyVehicle:
    def __init__(self):
        self.vehicle_id = "truck-1"
        self.status = VehicleStatus.IDLE
        self.max_weight_kg = 1000


class DummyOrder:
    def __init__(self):
        self.order_id = "order-1"

        self.pickup_node = 200
        self.pickup_lat = 1.301
        self.pickup_lon = 103.801

        self.delivery_node = 300
        self.delivery_lat = 1.302
        self.delivery_lon = 103.802

        self.weight_kg = 250


# ---------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------

@pytest.fixture
def builder():
    return RoutingProblemBuilder()


@pytest.fixture
def world():

    world = WorldState(
        graph=nx.MultiDiGraph(),
        depots=[DummyDepot()],
        vehicles=[DummyVehicle()],
        orders=[DummyOrder()],
    )

    world.graph = nx.MultiDiGraph()

    world.depots = [
        DummyDepot(),
    ]

    world.vehicles = [
        DummyVehicle(),
    ]

    world.orders = [
        DummyOrder(),
    ]

    return world


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_build_returns_routing_problem(builder, world):

    problem = builder.build(world)

    assert isinstance(problem, RoutingProblem)


def test_locations_created(builder, world):

    problem = builder.build(world)

    assert len(problem.locations) == 3

    assert problem.locations[0].kind == "depot"
    assert problem.locations[1].kind == "pickup"
    assert problem.locations[2].kind == "delivery"


def test_matrix_indices(builder, world):

    problem = builder.build(world)

    assert problem.locations[0].matrix_index == 0
    assert problem.locations[1].matrix_index == 1
    assert problem.locations[2].matrix_index == 2


def test_graph_nodes(builder, world):

    problem = builder.build(world)

    assert problem.locations[0].graph_node == 100
    assert problem.locations[1].graph_node == 200
    assert problem.locations[2].graph_node == 300


def test_starts(builder, world):

    problem = builder.build(world)

    assert problem.starts == [0]


def test_ends(builder, world):

    problem = builder.build(world)

    assert problem.ends == [0]


def test_demands(builder, world):

    problem = builder.build(world)

    assert problem.demands == [
        0,
        250,
        -250,
    ]


def test_capacities(builder, world):

    problem = builder.build(world)

    assert problem.capacities == [
        1000,
    ]


def test_vehicle_selection(builder, world):

    problem = builder.build(world)

    assert len(problem.vehicles) == 1

    assert problem.vehicles[0].vehicle_id == "truck-1"


def test_multiple_orders(builder, world):

    world.orders.append(
        DummyOrder()
    )

    world.orders[-1].order_id = "order-2"
    world.orders[-1].pickup_node = 400
    world.orders[-1].delivery_node = 500

    problem = builder.build(world)

    # depot + pickup1 + delivery1 + pickup2 + delivery2
    assert len(problem.locations) == 5

    assert problem.demands == [
        0,
        250,
        -250,
        250,
        -250,
    ]

def test_unavailable_vehicle_not_selected(builder, world):

    world.vehicles[0].status = VehicleStatus.OFFLINE

    problem = builder.build(world)

    assert len(problem.vehicles) == 0
    assert problem.capacities == []
    assert problem.starts == []
    assert problem.ends == []