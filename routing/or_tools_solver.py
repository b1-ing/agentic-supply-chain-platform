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
            vehicle_constraints=None,
            time_limit: int = 10,
    ):

        manager = pywrapcp.RoutingIndexManager(
            len(matrix),
            len(capacities),
            starts,
            ends,
        )

        routing = pywrapcp.RoutingModel(manager)


        ############################################################
        # Travel time
        ############################################################

        def transit_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)

            return int(matrix[from_node][to_node])

        transit_index = routing.RegisterTransitCallback(
            transit_callback
        )

        routing.SetArcCostEvaluatorOfAllVehicles(
            transit_index
        )

        ############################################################
        # Capacity
        ############################################################

        def demand_callback(index):

            node = manager.IndexToNode(index)

            return demands[node]

        demand_index = routing.RegisterUnaryTransitCallback(
            demand_callback
        )

        routing.AddDimensionWithVehicleCapacity(
            demand_index,
            0,
            capacities,
            True,
            "Capacity",
        )

        ############################################################
        # Time
        ############################################################

        routing.AddDimension(
            transit_index,
            9000,
            86400,
            False,
            "Time",
        )

        time_dimension = routing.GetDimensionOrDie(
            "Time"
        )

        ############################################################
        # Pickup / Delivery
        ############################################################

        for pair in pickup_delivery_pairs:

            pickup = pair.pickup
            delivery = pair.delivery

            pickup_idx = manager.NodeToIndex(pickup)
            delivery_idx = manager.NodeToIndex(delivery)

            routing.AddPickupAndDelivery(
                pickup_idx,
                delivery_idx,
            )

            routing.solver().Add(
                routing.VehicleVar(pickup_idx)
                ==
                routing.VehicleVar(delivery_idx)
            )

            routing.solver().Add(
                time_dimension.CumulVar(pickup_idx)
                <=
                time_dimension.CumulVar(delivery_idx)
            )

            if len(pair.allowed_vehicles) == 1:

                routing.solver().Add(
                    routing.VehicleVar(pickup_idx)
                    ==
                    pair.allowed_vehicles[0]
                )

                routing.solver().Add(
                    routing.VehicleVar(delivery_idx)
                    ==
                    pair.allowed_vehicles[0]
                )

            ########################################################
            # Vehicle compatibility
            ########################################################

            if vehicle_constraints is not None:

                allowed = pair["allowed_vehicles"]

                routing.VehicleVar(
                    pickup_idx
                ).SetValues(allowed)

                routing.VehicleVar(
                    delivery_idx
                ).SetValues(allowed)

        ############################################################
        # Search
        ############################################################

        search = pywrapcp.DefaultRoutingSearchParameters()

        search.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )

        search.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )

        search.time_limit.seconds = time_limit

        ############################################################
        # Solve
        ############################################################

        solution = routing.SolveWithParameters(search)

        if solution is None:
            return None

        for pair in pickup_delivery_pairs:

            pickup_idx = manager.NodeToIndex(pair.pickup)

            vehicle = solution.Value(
                routing.VehicleVar(pickup_idx)
            )

            print(
                f"{pair.order_id} -> vehicle {vehicle}"
            )

        return self._extract_routes(
            manager,
            routing,
            solution,
        )

    ################################################################

    def _extract_routes(
            self,
            manager,
            routing,
            solution,
    ):

        routes = []

        for vehicle in range(routing.vehicles()):

            route = []

            index = routing.Start(vehicle)

            while not routing.IsEnd(index):

                route.append(
                    manager.IndexToNode(index)
                )

                index = solution.Value(
                    routing.NextVar(index)
                )

            route.append(
                manager.IndexToNode(index)
            )

            routes.append(route)

        return routes