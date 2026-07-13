class RouteBuilder:

    def build(
        self,
        world,
        travel_matrix: TravelMatrix,
        vehicles: list[Vehicle],
        routes: list[list[int]],
    ) -> RoutePlan:


    def _build_stops(
        self,
        travel_matrix: TravelMatrix,
        route: list[int],
    ) -> list[RouteStop]:
        stops = []

        for sequence, matrix_index in enumerate(route):

            location = travel_matrix.locations[matrix_index]

            stop = RouteStop(
                sequence=sequence,
                location=location,
            )

            stops.append(stop)

        return stops

    def _build_segments(
        self,
        world,
        stops: list[RouteStop],
    ) -> list[RouteSegment]:
        for current, nxt in zip(stops, stops[1:]):
            from_node = current.location.graph_node
            to_node = nxt.location.graph_node
            path = nx.shortest_path(
                world.graph,
                from_node,
                to_node,
                weight="travel_time",
            )
