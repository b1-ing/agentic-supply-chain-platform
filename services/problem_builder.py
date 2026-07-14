from models.routing_problem import RoutingProblem
from models.world_state import WorldState
from routing_location import RoutingLocation
from vehicles.vehicle import Vehicle


class RoutingProblemBuilder:

    def build(
            self,
            world,
    ) -> RoutingProblem:

        vehicles = self._select_vehicles(world)

        locations = self._build_locations(
            world,
            vehicles,
        )

        starts = self._build_starts(
            vehicles,
            locations,
        )

        ends = self._build_ends(
            vehicles,
            locations,
        )

        demands = self._build_demands(
            world,
            locations,
        )

        capacities = self._build_capacities(
            vehicles,
        )

        return RoutingProblem(...)

    def _select_vehicles(world: WorldState):
        """
        Filters all the vehicles available according to their availability.

        :params:
        world: World object

        :return:
        available_vehicles: list of vehicle objects
        """
        available_vehicles = []
        for vehicle in world.vehicles:
            if vehicle.status == Vehicle.Status.AVAILABLE:
                available_vehicles.append(vehicle)
        return available_vehicles
    def _build_locations(
            self,
            world: WorldState,
    ) -> list[RoutingLocation]:

        locations: list[RoutingLocation] = []

        self._build_depots(world, locations)
        self._build_pickups(world, locations)
        self._build_deliveries(world, locations)

        return locations


    def _build_depots(
            self,
            world: WorldState,
            locations: list[RoutingLocation],
    ) -> None:

        for depot in world.depots:

            locations.append(
                RoutingLocation(
                    matrix_index=len(locations),
                    graph_node=depot.graph_node,
                    lat=depot.lat,
                    lon=depot.lon,
                    kind="depot",
                )
            )


    def _build_pickups(
            self,
            world: WorldState,
            locations: list[RoutingLocation],
    ) -> None:

        for order in world.orders:

            locations.append(
                RoutingLocation(
                    matrix_index=len(locations),
                    graph_node=order.pickup_node,
                    lat=order.pickup_lat,
                    lon=order.pickup_lon,
                    kind="pickup",
                    order_id=order.order_id,
                )
            )


    def _build_deliveries(
            self,
            world: WorldState,
            locations: list[RoutingLocation],
    ) -> None:

        for order in world.orders:

            locations.append(
                RoutingLocation(
                    matrix_index=len(locations),
                    graph_node=order.delivery_node,
                    lat=order.delivery_lat,
                    lon=order.delivery_lon,
                    kind="delivery",
                    order_id=order.order_id,
                )
            )

    def _build_starts(
            self,
            vehicles: list[Vehicle],
            locations: list[RoutingLocation],
    ) -> list[int]:

        depot_index = next(
            location.matrix_index
            for location in locations
            if location.kind == "depot"
        )

        return [depot_index for _ in vehicles]

    def _build_demands(
            self,
            world: WorldState,
            locations: list[RoutingLocation],
    ) -> list[int]:

        order_lookup = {
            order.order_id: order
            for order in world.orders
        }

        demands = []

        for location in locations:

            if location.kind == "depot":
                demands.append(0)
                continue

            order = order_lookup[location.order_id]

            weight = int(order.weight_kg or 0)

            if location.kind == "pickup":
                demands.append(weight)

            else:
                demands.append(-weight)

        return demands










