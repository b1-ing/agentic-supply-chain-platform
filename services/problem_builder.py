from models.routing_problem import RoutingProblem
from models.world_state import WorldState
from models.routing_location import RoutingLocation
from models.vehicles.vehicle import Vehicle, VehicleStatus


class RoutingProblemBuilder:

    def build(
            self,
            world,
    ) -> RoutingProblem:

        vehicles = self._select_vehicles(world)

        locations = self._build_locations(
            world,
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

        pickup_delivery_pairs = self._build_pickup_delivery_pairs(
            world,
            locations,
        )

        return RoutingProblem(
            vehicles=vehicles,
            locations=locations,
            starts=starts,
            ends=ends,
            demands=demands,
            capacities=capacities,
            pickup_delivery_pairs=pickup_delivery_pairs,
        )

    def _select_vehicles(
            self,
            world: WorldState
    ):
        """
        Filters all the vehicles available according to their availability.

        :params:
        world: World object

        :return:
        available_vehicles: list of vehicle objects
        """
        available_vehicles = []
        for vehicle in world.vehicles:
            if vehicle.status == VehicleStatus.IDLE:
                available_vehicles.append(vehicle)
        return available_vehicles

    def _build_locations(
            self,
            world: WorldState,
    ) -> list[RoutingLocation]:

        locations: list[RoutingLocation] = []

        self._build_depots(world, locations)
        self._build_order_points(world, locations)
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


    def _build_order_points(
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

        """

        :param vehicles:
        :param locations:
        :return:
        """

        depot_index = next(
            location.matrix_index
            for location in locations
            if location.kind == "depot"
        )

        return [depot_index for _ in vehicles]

    def _build_ends(
            self,
            vehicles,
            locations,
    ):

        depot_index = next(
            location.matrix_index
            for location in locations
            if location.kind == "depot"
        )

        return [depot_index for _ in vehicles]

    def _build_capacities(
            self,
            vehicles: list[Vehicle],
    ) -> list[int]:

        return [
            int(vehicle.max_weight_kg)
            for vehicle in vehicles
        ]

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

    def _build_pickup_delivery_pairs(
            self,
            world,
            locations,
    ) -> list[tuple[int, int]]:

        pickup_indices = {}
        delivery_indices = {}

        for index, location in enumerate(locations):

            if location.kind == "pickup":
                pickup_indices[location.order_id] = index

            elif location.kind == "delivery":
                delivery_indices[location.order_id] = index

        pairs = []

        for order in world.orders:
            pairs.append(
                (
                    pickup_indices[order.order_id],
                    delivery_indices[order.order_id],
                )
            )

        return pairs










