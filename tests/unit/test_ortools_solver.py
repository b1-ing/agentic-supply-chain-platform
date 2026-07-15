import numpy as np

from routing.or_tools_solver import ORToolsSolver


def test_solver_returns_valid_routes():
    """
    Simple CVRP instance.

    Matrix indices

        0 Depot
        1 Customer A
        2 Customer B
        3 Customer C
    """

    matrix = np.array(
        [
            [0, 5, 7, 8],
            [5, 0, 2, 4],
            [7, 2, 0, 3],
            [8, 4, 3, 0],
        ]
    )

    starts = [0, 0]
    ends = [0, 0]

    demands = [
        0,      # depot
        20,
        30,
        10,
    ]

    capacities = [
        100,
        100,
    ]

    solver = ORToolsSolver()

    print(matrix)
    print(matrix.dtype)

    print(np.isinf(matrix).any())
    print(np.isnan(matrix).any())

    routes = solver.solve(
        matrix=matrix,
        starts=starts,
        ends=ends,
        demands=demands,
        capacities=capacities,
    )

    assert routes is not None

    #
    # One route per vehicle
    #

    assert len(routes) == 2

    #
    # Every route starts and ends at the depot
    #

    for route in routes:
        assert route[0] == 0
        assert route[-1] == 0

    #
    # Collect all customer visits
    #

    visited = []

    for route in routes:
        visited.extend(
            node
            for node in route
            if node != 0
        )

    #
    # Every customer visited exactly once
    #

    assert sorted(visited) == [1, 2, 3]

    #
    # No duplicates
    #

    assert len(visited) == len(set(visited))

def test_solver_respects_capacity():

    matrix = np.array(
        [
            [0, 5, 5],
            [5, 0, 2],
            [5, 2, 0],
        ]
    )

    starts = [0]
    ends = [0]

    demands = [0, 80, 80]

    capacities = [100]

    solver = ORToolsSolver()

    routes = solver.solve(
        matrix=matrix,
        starts=starts,
        ends=ends,
        demands=demands,
        capacities=capacities,
        time_limit=2,
    )

    # Total demand (160) exceeds vehicle capacity (100),
    # so there should be no feasible solution.

    assert routes is None