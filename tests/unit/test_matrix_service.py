import networkx as nx
import numpy as np
import pytest
from unittest.mock import MagicMock

from models.routing_location import RoutingLocation
from routing.matrix_service import MatrixService


@pytest.fixture
def matrix_service():
    return MatrixService()


@pytest.fixture
def mock_world():
    """Creates a mock world object with a basic NetworkX graph."""
    world = MagicMock()
    G = nx.DiGraph()

    # Create a simple weighted graph: Node 0 -> Node 1 (weight 5), Node 1 -> Node 2 (weight 10)
    # Node 2 cannot reach Node 0 (should result in np.inf)
    G.add_edge(0, 1, travel_time=5)
    G.add_edge(1, 2, travel_time=10)
    G.add_edge(0, 2, travel_time=20)  # Direct path, but longer than 5 + 10

    world.graph = G
    return world


@pytest.fixture
def mock_locations():
    """Creates a list of 3 mock RoutingLocation objects mapping to graph nodes 0, 1, and 2."""
    loc0 = MagicMock(spec=RoutingLocation)
    loc0.graph_node = 0

    loc1 = MagicMock(spec=RoutingLocation)
    loc1.graph_node = 1

    loc2 = MagicMock(spec=RoutingLocation)
    loc2.graph_node = 2

    return [loc0, loc1, loc2]


def test_matrix_service_build_dimensions(matrix_service, mock_world, mock_locations):
    """Test that the output matrix has the correct shape and contains the original locations."""
    result = matrix_service.build(mock_world, mock_locations)

    assert result.matrix.shape == (3, 3)
    assert result.locations == mock_locations


def test_matrix_service_shortest_paths(matrix_service, mock_world, mock_locations):
    """Test that the travel times match expected Dijkstra shortest path weights."""
    result = matrix_service.build(mock_world, mock_locations)
    matrix = result.matrix

    # Diagonal (self-travel) should always be 0
    assert matrix[0, 0] == 0
    assert matrix[1, 1] == 0
    assert matrix[2, 2] == 0

    # Node 0 to Node 1 (direct edge weight is 5)
    assert matrix[0, 1] == 5

    # Node 0 to Node 2 (via Node 1 is 5 + 10 = 15, which is faster than the direct 20)
    assert matrix[0, 2] == 15

    # Node 1 to Node 2 (direct edge weight is 10)
    assert matrix[1, 2] == 10


def test_matrix_service_unreachable_nodes(matrix_service, mock_world, mock_locations):
    """Test that unreachable pairs result in np.inf."""
    result = matrix_service.build(mock_world, mock_locations)
    matrix = result.matrix

    # Node 2 has no outgoing edges to Node 0 or Node 1
    assert matrix[2, 0] == np.inf
    assert matrix[2, 1] == np.inf


def test_matrix_service_empty_locations(matrix_service, mock_world):
    """Test behavior when an empty list of locations is passed."""
    result = matrix_service.build(mock_world, [])

    assert result.matrix.shape == (0, 0)
    assert len(result.locations) == 0


def test_matrix_service_locations_contents(matrix_service, mock_world):
    """Test that the returned locations preserve their metadata."""

    depot = RoutingLocation(
        matrix_index=0,
        graph_node=100,
        lat=1.300,
        lon=103.800,
        kind="depot",
        order_id=None,
        vehicle_id="vehicle_1",
    )

    pickup = RoutingLocation(
        matrix_index=1,
        graph_node=200,
        lat=1.310,
        lon=103.810,
        kind="pickup",
        order_id="order_123",
        vehicle_id=None,
    )

    # Graph needs matching nodes
    mock_world.graph.add_node(100)
    mock_world.graph.add_node(200)

    result = matrix_service.build(
        mock_world,
        [depot, pickup],
    )

    assert len(result.locations) == 2

    assert result.locations[0].graph_node == 100
    assert result.locations[0].lat == 1.300
    assert result.locations[0].lon == 103.800
    assert result.locations[0].kind == "depot"
    assert result.locations[0].vehicle_id == "vehicle_1"

    assert result.locations[1].graph_node == 200
    assert result.locations[1].kind == "pickup"
    assert result.locations[1].order_id == "order_123"
