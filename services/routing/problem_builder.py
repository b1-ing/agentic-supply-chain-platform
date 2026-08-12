from models.routing.routing_problem import RoutingProblem
from models.world.world_state import WorldState
from models.order.routing_location import RoutingLocation
from models.vehicles.vehicle import Vehicle, VehicleStatus
from models.routing.pickup_delivery_pair import PickupDeliveryPair
from models.order.incoming_order import OrderStatus
from models.routing.compatibility_result import CompatibilityStatus


class RoutingProblemBuilder:
    def build(
        self,
        world: WorldState,
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

    ####################################################################
    # Vehicles
    ####################################################################
    ####################################################################
    # Vehicles
    ####################################################################

    def _select_vehicles(
        self,
        world: WorldState,
    ) -> list[Vehicle]:

        # Return every vehicle.
        # Compatibility + availability are handled later.
        return world.vehicles

    def _build_pickup_delivery_pairs(
        self,
        world: WorldState,
        locations: list[RoutingLocation],
    ) -> list[PickupDeliveryPair]:

        pickups = {l.order_id: l.matrix_index for l in locations if l.kind == "pickup"}

        deliveries = {
            l.order_id: l.matrix_index for l in locations if l.kind == "delivery"
        }

        pairs = []

        for order in world.new_orders:
            compatibility = world.compatibility_results[order.order_id]

            print(compatibility)

            if compatibility.status != CompatibilityStatus.ROUTABLE:
                continue

            pairs.append(
                PickupDeliveryPair(
                    order_id=order.order_id,
                    pickup=pickups[order.order_id],
                    delivery=deliveries[order.order_id],
                    allowed_vehicles=compatibility.allowed_vehicle_indices,
                )
            )

        return pairs

    def _failure_reason(
        self,
        vehicle,
        order,
    ) -> str | None:

        if order.refrigerated and not vehicle.refrigerated:
            return "Vehicle is not refrigerated."

        if order.height_m and order.height_m > vehicle.height_m:
            return "Vehicle height exceeded."

        if order.weight_kg and order.weight_kg > vehicle.max_weight_kg:
            return "Vehicle weight exceeded."

        if order.hazardous and not vehicle.hazardous_certified:
            return "Vehicle is not hazardous-certified."

        return None

    ####################################################################
    # Locations
    ####################################################################

    def _build_locations(
        self,
        world: WorldState,
        vehicles: list[Vehicle],
    ) -> list[RoutingLocation]:

        locations = []

        self._build_vehicle_locations(
            world,
            vehicles,
            locations,
        )

        self._build_order_locations(
            world,
            locations,
        )

        return locations

    def _build_vehicle_locations(
        self,
        world: WorldState,
        vehicles: list[Vehicle],
        locations: list[RoutingLocation],
    ):

        for vehicle in vehicles:
            if vehicle.current_node is None:
                raise ValueError(f"Vehicle {vehicle.vehicle_id} has no current_node.")

            locations.append(
                RoutingLocation(
                    matrix_index=len(locations),
                    graph_node=vehicle.current_node,
                    lat=world.graph.nodes[vehicle.current_node]["y"],
                    lon=world.graph.nodes[vehicle.current_node]["x"],
                    kind="vehicle",
                )
            )

    def _build_order_locations(
        self,
        world: WorldState,
        locations: list[RoutingLocation],
    ):

        for order in world.new_orders:
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

    ####################################################################
    # Starts / Ends
    ####################################################################

    def _build_starts(
        self,
        vehicles: list[Vehicle],
        locations: list[RoutingLocation],
    ) -> list[int]:

        return list(range(len(vehicles)))

    def _build_ends(
        self,
        vehicles: list[Vehicle],
        locations: list[RoutingLocation],
    ) -> list[int]:

        return list(range(len(vehicles)))

    ####################################################################
    # Capacities
    ####################################################################

    def _build_capacities(
        self,
        vehicles: list[Vehicle],
    ) -> list[int]:

        return [int(vehicle.max_weight_kg) for vehicle in vehicles]

    ####################################################################
    # Demands
    ####################################################################

    def _build_demands(
        self,
        world: WorldState,
        locations: list[RoutingLocation],
    ) -> list[int]:

        order_lookup = {order.order_id: order for order in world.new_orders}

        demands = []

        for location in locations:
            if location.kind == "vehicle":
                demands.append(0)
                continue

            order = order_lookup[location.order_id]

            weight = int(order.weight_kg or 0)

            if location.kind == "pickup":
                demands.append(weight)
            else:
                demands.append(-weight)

        return demands

    ####################################################################
    # Pickup / Delivery
    ####################################################################
    #
    # def _build_pickup_delivery_pairs(
    #         self,
    #         world: WorldState,
    #         locations: list[RoutingLocation],
    # ) -> list[tuple[int, int]]:
    #
    #     pickups = {}
    #     deliveries = {}
    #
    #     for location in locations:
    #
    #         if location.kind == "pickup":
    #             pickups[location.order_id] = location.matrix_index
    #
    #         elif location.kind == "delivery":
    #             deliveries[location.order_id] = location.matrix_index
    #
    #     return [
    #         (
    #             pickups[order.order_id],
    #             deliveries[order.order_id],
    #         )
    #         for order in world.new_orders
    #     ]
