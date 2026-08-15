from __future__ import annotations

from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2


class ORToolsSolver:
    """
    OR-Tools CVRP solver.

    Responsibilities
    ----------------
    - Build the OR-Tools routing model.
    - Apply travel-time costs.
    - Apply vehicle capacity constraints.
    - Apply pickup/delivery constraints.
    - Restrict orders to compatible vehicles.
    - Solve the fleet routing problem.
    - Return routes as matrix-index sequences.

    This class does NOT:
    - build the routing problem
    - build the travel matrix
    - perform compatibility evaluation
    - create VehicleRoute objects
    - modify WorldState
    """

    def solve(
        self,
        matrix,
        starts,
        ends,
        demands,
        capacities,
        pickup_delivery_pairs,
        vehicle_constraints=None,
        time_limit: int = 10,
    ):
        """
        Solve the fleet routing problem.

        Returns
        -------
        list[list[int]] | None
            One route per vehicle.

        Example:

            [
                [0, 3, 4, 0],
                [1, 5, 6, 1],
            ]

        Each number is an index into TravelMatrix.locations.
        """

        # --------------------------------------------------------------
        # Validate basic problem dimensions
        # --------------------------------------------------------------

        self._validate_inputs(
            matrix=matrix,
            starts=starts,
            ends=ends,
            demands=demands,
            capacities=capacities,
            pickup_delivery_pairs=pickup_delivery_pairs,
        )

        # --------------------------------------------------------------
        # Build routing manager
        # --------------------------------------------------------------

        manager = pywrapcp.RoutingIndexManager(
            len(matrix),
            len(capacities),
            starts,
            ends,
        )

        routing = pywrapcp.RoutingModel(manager)

        # --------------------------------------------------------------
        # Travel-time cost
        # --------------------------------------------------------------

        transit_index = routing.RegisterTransitCallback(
            lambda from_index, to_index: self._transit_callback(
                manager,
                matrix,
                from_index,
                to_index,
            )
        )

        routing.SetArcCostEvaluatorOfAllVehicles(
            transit_index
        )

        # --------------------------------------------------------------
        # Vehicle capacity
        # --------------------------------------------------------------

        demand_index = routing.RegisterUnaryTransitCallback(
            lambda index: self._demand_callback(
                manager,
                demands,
                index,
            )
        )

        routing.AddDimensionWithVehicleCapacity(
            demand_index,
            0,                  # no slack
            capacities,
            True,               # start cumul at zero
            "Capacity",
        )

        # --------------------------------------------------------------
        # Travel-time dimension
        # --------------------------------------------------------------

        routing.AddDimension(
            transit_index,
            9000,               # waiting/slack
            86400,              # maximum route time
            False,              # do not force start to zero
            "Time",
        )

        time_dimension = routing.GetDimensionOrDie(
            "Time"
        )

        # --------------------------------------------------------------
        # Pickup / Delivery
        # --------------------------------------------------------------

        self._add_pickup_delivery_constraints(
            routing=routing,
            manager=manager,
            time_dimension=time_dimension,
            pickup_delivery_pairs=pickup_delivery_pairs,
        )

        # --------------------------------------------------------------
        # Search configuration
        # --------------------------------------------------------------

        search = pywrapcp.DefaultRoutingSearchParameters()

        search.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        search.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )

        search.time_limit.seconds = max(
            1,
            int(time_limit),
        )

        # --------------------------------------------------------------
        # Solve
        # --------------------------------------------------------------

        solution = routing.SolveWithParameters(
            search
        )

        if solution is None:
            return None

        # --------------------------------------------------------------
        # Debug assignment information
        # --------------------------------------------------------------

        self._print_assignments(
            manager=manager,
            routing=routing,
            solution=solution,
            pickup_delivery_pairs=pickup_delivery_pairs,
        )

        # --------------------------------------------------------------
        # Extract routes
        # --------------------------------------------------------------

        return self._extract_routes(
            manager=manager,
            routing=routing,
            solution=solution,
        )

    # ==================================================================
    # Transit
    # ==================================================================

    @staticmethod
    def _transit_callback(
        manager,
        matrix,
        from_index,
        to_index,
    ) -> int:
        """
        Return travel time between two matrix nodes.

        OR-Tools requires an integer cost.

        Unreachable edges are represented by infinity in MatrixService.
        Those edges receive a very large penalty instead of causing:

            OverflowError: cannot convert float infinity to integer
        """

        from_node = manager.IndexToNode(
            from_index
        )

        to_node = manager.IndexToNode(
            to_index
        )

        value = matrix[
            from_node
        ][
            to_node
        ]

        if value == float("inf"):
            return 10**9

        if value != value:
            # NaN
            return 10**9

        return max(
            0,
            int(value),
        )

    # ==================================================================
    # Demand
    # ==================================================================

    @staticmethod
    def _demand_callback(
        manager,
        demands,
        index,
    ) -> int:

        node = manager.IndexToNode(
            index
        )

        return int(
            demands[node]
        )

    # ==================================================================
    # Pickup / Delivery
    # ==================================================================

    @staticmethod
    def _add_pickup_delivery_constraints(
        routing,
        manager,
        time_dimension,
        pickup_delivery_pairs,
    ):
        """
        Add pickup/delivery constraints.

        For every order:

            pickup
                ↓
            delivery

        The pickup and delivery must:

        1. be served by the same vehicle
        2. occur in the correct order
        3. only use compatible vehicles
        """

        for pair in pickup_delivery_pairs:

            pickup_index = manager.NodeToIndex(
                pair.pickup
            )

            delivery_index = manager.NodeToIndex(
                pair.delivery
            )

            # ----------------------------------------------------------
            # Pickup and delivery belong to the same vehicle.
            # ----------------------------------------------------------

            routing.AddPickupAndDelivery(
                pickup_index,
                delivery_index,
            )

            routing.solver().Add(
                routing.VehicleVar(
                    pickup_index
                )
                ==
                routing.VehicleVar(
                    delivery_index
                )
            )

            # ----------------------------------------------------------
            # Pickup must occur before delivery.
            # ----------------------------------------------------------

            routing.solver().Add(
                time_dimension.CumulVar(
                    pickup_index
                )
                <=
                time_dimension.CumulVar(
                    delivery_index
                )
            )

            # ----------------------------------------------------------
            # Restrict the pair to compatible vehicles.
            # ----------------------------------------------------------

            allowed_vehicles = list(
                pair.allowed_vehicles
            )

            if not allowed_vehicles:
                raise ValueError(
                    f"Order {pair.order_id} has no "
                    f"compatible vehicles."
                )

            routing.VehicleVar(
                pickup_index
            ).SetValues(
                allowed_vehicles
            )

            routing.VehicleVar(
                delivery_index
            ).SetValues(
                allowed_vehicles
            )

    # ==================================================================
    # Assignment debugging
    # ==================================================================

    @staticmethod
    def _print_assignments(
        manager,
        routing,
        solution,
        pickup_delivery_pairs,
    ):
        """
        Print which vehicle OR-Tools assigned to each order.
        """

        for pair in pickup_delivery_pairs:

            pickup_index = manager.NodeToIndex(
                pair.pickup
            )

            vehicle_index = solution.Value(
                routing.VehicleVar(
                    pickup_index
                )
            )

            print(
                f"[CVRP] "
                f"{pair.order_id} "
                f"-> vehicle index "
                f"{vehicle_index}"
            )

    # ==================================================================
    # Route extraction
    # ==================================================================

    @staticmethod
    def _extract_routes(
        manager,
        routing,
        solution,
    ) -> list[list[int]]:
        """
        Convert OR-Tools solution into matrix-index routes.

        Every vehicle receives one route, including vehicles that
        remain unused.

        Example:

            [
                [0, 3, 4, 0],
                [1, 1],
                [2, 5, 6, 2],
            ]
        """

        routes = []

        for vehicle_index in range(
            routing.vehicles()
        ):

            route = []

            index = routing.Start(
                vehicle_index
            )

            while not routing.IsEnd(index):

                route.append(
                    manager.IndexToNode(index)
                )

                index = solution.Value(
                    routing.NextVar(index)
                )

            # Include final depot/end node.
            route.append(
                manager.IndexToNode(index)
            )

            routes.append(route)

        return routes

    # ==================================================================
    # Validation
    # ==================================================================

    @staticmethod
    def _validate_inputs(
        matrix,
        starts,
        ends,
        demands,
        capacities,
        pickup_delivery_pairs,
    ):
        """
        Validate the problem before passing it to OR-Tools.
        """

        if matrix is None:
            raise ValueError(
                "Routing matrix is None."
            )

        node_count = len(matrix)

        if node_count == 0:
            raise ValueError(
                "Routing matrix is empty."
            )

        if len(starts) != len(capacities):
            raise ValueError(
                "Number of starts must match "
                "number of vehicles."
            )

        if len(ends) != len(capacities):
            raise ValueError(
                "Number of ends must match "
                "number of vehicles."
            )

        if len(demands) != node_count:
            raise ValueError(
                "Number of demands must match "
                "number of matrix nodes."
            )

        for start in starts:

            if start < 0 or start >= node_count:
                raise ValueError(
                    f"Invalid vehicle start index: {start}"
                )

        for end in ends:

            if end < 0 or end >= node_count:
                raise ValueError(
                    f"Invalid vehicle end index: {end}"
                )

        for pair in pickup_delivery_pairs:

            if pair.pickup < 0 or pair.pickup >= node_count:
                raise ValueError(
                    f"Invalid pickup index "
                    f"{pair.pickup} for order "
                    f"{pair.order_id}."
                )

            if pair.delivery < 0 or pair.delivery >= node_count:
                raise ValueError(
                    f"Invalid delivery index "
                    f"{pair.delivery} for order "
                    f"{pair.order_id}."
                )

            for vehicle_index in pair.allowed_vehicles:

                if (
                    vehicle_index < 0
                    or vehicle_index >= len(capacities)
                ):
                    raise ValueError(
                        f"Invalid vehicle index "
                        f"{vehicle_index} for order "
                        f"{pair.order_id}."
                    )