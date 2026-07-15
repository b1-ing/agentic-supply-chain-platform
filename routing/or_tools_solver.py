from ortools.constraint_solver import pywrapcp
from ortools.constraint_solver import routing_enums_pb2


class ORToolsSolver:

    def solve(
        self,
        matrix,
        starts,
        ends,
        demands,
        capacities,
        pickup_delivery_pairs,
        time_limit: int = 10,

    ):
        """
        Solve a Capacitated Vehicle Routing Problem (CVRP).

        Parameters:

        matrix
            NxN travel-time matrix.

        starts
            Matrix index where each vehicle starts.

        ends
            Matrix index where each vehicle ends.

        demands
            Demand for every matrix node.

        capacities
            Capacity of each vehicle.

        Returns
        -------
        list[list[int]]

            One list of matrix indices per vehicle.

            Example:

            [
                [0, 3, 5, 0],
                [0, 1, 2, 4, 0],
            ]
        """

        manager = pywrapcp.RoutingIndexManager(
            len(matrix),
            len(capacities),
            starts,
            ends,
        )

        print("Number of nodes:", manager.GetNumberOfNodes())
        print("Number of vehicles:", len(capacities))
        print("Starts:", starts)
        print("Ends:", ends)

        for i in range(10):
            try:
                print(i, "->", manager.IndexToNode(i))
            except Exception as e:
                print(i, e)

        routing = pywrapcp.RoutingModel(manager)


        for pickup, delivery in pickup_delivery_pairs:
            pickup_idx = manager.NodeToIndex(pickup)
            delivery_idx = manager.NodeToIndex(delivery)

            routing.AddPickupAndDelivery(pickup_idx, delivery_idx)

            routing.solver().Add(
            routing.VehicleVar(pickup_idx) ==
            routing.VehicleVar(delivery_idx)
            )

            routing.solver().Add(
            routing.CumulVar(pickup_idx) <=
            routing.CumulVar(delivery_idx)
            )

        # --------------------------------------------------
        # Travel cost callback
        # --------------------------------------------------
        """
        Transit callback: a function that takes any pair of locations and returns the distance between them.
        """
        def transit_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)

            return int(matrix[from_node][to_node])

        transit_callback_index = routing.RegisterTransitCallback(
            transit_callback
        )


        """
        The arc cost evaluator tells the solver how to calculate the cost of travel between any two locations.
        In other words, the cost of the edge (or arc) joining them in the graph for the problem.
        """
        routing.SetArcCostEvaluatorOfAllVehicles(
            transit_callback_index
        )

        # --------------------------------------------------
        # Capacity constraint
        # --------------------------------------------------

        def demand_callback(index):

            node = manager.IndexToNode(index)

            return demands[node]

        demand_callback_index = routing.RegisterUnaryTransitCallback(
            demand_callback
        )

        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,                  # slack
            capacities,
            True,
            "Capacity",
        )

        # --------------------------------------------------
        # Search parameters
        # --------------------------------------------------

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()

        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )

        search_parameters.time_limit.seconds = time_limit

        # --------------------------------------------------
        # Solve
        # --------------------------------------------------

        solution = routing.SolveWithParameters(
            search_parameters
        )

        if solution is None:
            return None

        return self._extract_routes(
            manager,
            routing,
            solution,
        )

    def _extract_routes(
        self,
        manager,
        routing,
        solution,
    ):
        """
        Convert OR-Tools solution into matrix indices.
        """

        routes = []

        for vehicle_id in range(routing.vehicles()):

            route = []

            index = routing.Start(vehicle_id)

            while not routing.IsEnd(index):
                print("routing index:", index)
                route.append(
                    manager.IndexToNode(index)
                )

                index = solution.Value(
                    routing.NextVar(index)
                )
            print("end routing index:", index)
            route.append(
                manager.IndexToNode(index)
            )

            routes.append(route)

        return routes