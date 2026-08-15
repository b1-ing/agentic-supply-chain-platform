from __future__ import annotations

from models.routing.routing_problem import RoutingProblem
from models.world.world_state import WorldState
from models.order.routing_location import RoutingLocation
from models.vehicles.vehicle import Vehicle, VehicleStatus
from models.routing.pickup_delivery_pair import PickupDeliveryPair
from models.routing.compatibility_result import CompatibilityStatus


class RoutingProblemBuilder:
    """
    Converts WorldState into an OR-Tools routing problem.

    Responsibilities
    ----------------
    - Select vehicles that can participate in optimisation.
    - Select routable orders.
    - Build vehicle start/end locations.
    - Build pickup/delivery locations.
    - Build capacity demands.
    - Convert compatible vehicle IDs into OR-Tools vehicle indices.
    - Build pickup/delivery constraints.

    This class does NOT:
    - evaluate compatibility
    - call an LLM
    - solve the routing problem
    - mutate order lifecycle state
    """

    def build(
        self,
        world: WorldState,
    ) -> RoutingProblem:

        vehicles = self._select_vehicles(
            world
        )

        if not vehicles:
            return RoutingProblem(
                vehicles=[],
                locations=[],
                starts=[],
                ends=[],
                demands=[],
                capacities=[],
                pickup_delivery_pairs=[],
            )

        routable_orders = self._select_orders(
            world
        )

        locations = self._build_locations(
            world,
            vehicles,
            routable_orders,
        )

        starts = self._build_starts(
            vehicles
        )

        ends = self._build_ends(
            vehicles
        )

        demands = self._build_demands(
            routable_orders,
            locations,
        )

        capacities = self._build_capacities(
            vehicles
        )

        pickup_delivery_pairs = (
            self._build_pickup_delivery_pairs(
                world,
                vehicles,
                routable_orders,
                locations,
            )
        )

        return RoutingProblem(
            vehicles=vehicles,
            locations=locations,
            starts=starts,
            ends=ends,
            demands=demands,
            capacities=capacities,
            pickup_delivery_pairs=(
                pickup_delivery_pairs
            ),
        )

    # ================================================================
    # ORDERS
    # ================================================================

    @staticmethod
    def _select_orders(
        world: WorldState,
    ):
        """
        Select only orders that are currently routable.

        Waiting / uncertain orders are deliberately excluded.
        """

        routable_orders = []

        for order in world.new_orders:

            compatibility = (
                world.compatibility_results.get(
                    order.order_id
                )
            )

            if compatibility is None:
                continue

            if (
                compatibility.status
                != CompatibilityStatus.ROUTABLE
            ):
                continue

            routable_orders.append(order)

        return routable_orders

    # ================================================================
    # VEHICLES
    # ================================================================

    @staticmethod
    def _select_vehicles(
        world: WorldState,
    ) -> list[Vehicle]:
        """
        Select vehicles that are available for fleet optimisation.

        OR-Tools vehicle indices are based on THIS list.

        Therefore:

            index 0 → vehicles[0]
            index 1 → vehicles[1]
            ...

        Compatibility vehicle IDs are converted into these indices
        later in _build_pickup_delivery_pairs().
        """

        return [
            vehicle
            for vehicle in world.vehicles
            if vehicle.status == VehicleStatus.IDLE
            and vehicle.current_node is not None
        ]

    # ================================================================
    # LOCATIONS
    # ================================================================

    def _build_locations(
        self,
        world: WorldState,
        vehicles: list[Vehicle],
        orders,
    ) -> list[RoutingLocation]:

        locations: list[RoutingLocation] = []

        self._build_vehicle_locations(
            world,
            vehicles,
            locations,
        )

        self._build_order_locations(
            orders,
            locations,
        )

        return locations

    # ---------------------------------------------------------------
    # Vehicle locations
    # ---------------------------------------------------------------

    @staticmethod
    def _build_vehicle_locations(
        world: WorldState,
        vehicles: list[Vehicle],
        locations: list[RoutingLocation],
    ) -> None:

        for vehicle in vehicles:

            node = vehicle.current_node

            if node is None:
                raise ValueError(
                    f"Vehicle {vehicle.vehicle_id} "
                    "has no current_node."
                )

            node_data = world.graph.nodes[node]

            locations.append(
                RoutingLocation(
                    matrix_index=len(locations),
                    graph_node=node,
                    lat=float(node_data["y"]),
                    lon=float(node_data["x"]),
                    kind="vehicle",
                )
            )

    # ---------------------------------------------------------------
    # Order locations
    # ---------------------------------------------------------------

    @staticmethod
    def _build_order_locations(
        orders,
        locations: list[RoutingLocation],
    ) -> None:

        for order in orders:

            if order.pickup_node is None:
                raise ValueError(
                    f"Order {order.order_id} "
                    "has no pickup graph node."
                )

            if order.delivery_node is None:
                raise ValueError(
                    f"Order {order.order_id} "
                    "has no delivery graph node."
                )

            if (
                order.pickup_lat is None
                or order.pickup_lon is None
            ):
                raise ValueError(
                    f"Order {order.order_id} "
                    "has no pickup coordinates."
                )

            if (
                order.delivery_lat is None
                or order.delivery_lon is None
            ):
                raise ValueError(
                    f"Order {order.order_id} "
                    "has no delivery coordinates."
                )

            # --------------------------------------------------------
            # Pickup
            # --------------------------------------------------------

            locations.append(
                RoutingLocation(
                    matrix_index=len(locations),
                    graph_node=order.pickup_node,
                    lat=float(order.pickup_lat),
                    lon=float(order.pickup_lon),
                    kind="pickup",
                    order_id=order.order_id,
                )
            )

            # --------------------------------------------------------
            # Delivery
            # --------------------------------------------------------

            locations.append(
                RoutingLocation(
                    matrix_index=len(locations),
                    graph_node=order.delivery_node,
                    lat=float(order.delivery_lat),
                    lon=float(order.delivery_lon),
                    kind="delivery",
                    order_id=order.order_id,
                )
            )

    # ================================================================
    # STARTS / ENDS
    # ================================================================

    @staticmethod
    def _build_starts(
        vehicles: list[Vehicle],
    ) -> list[int]:
        """
        Vehicle locations are inserted first into the location list.

        Therefore:

            vehicle 0 → location 0
            vehicle 1 → location 1
            vehicle 2 → location 2
        """

        return list(
            range(len(vehicles))
        )

    @staticmethod
    def _build_ends(
        vehicles: list[Vehicle],
    ) -> list[int]:
        """
        Each vehicle returns to its own starting location.
        """

        return list(
            range(len(vehicles))
        )

    # ================================================================
    # CAPACITIES
    # ================================================================

    @staticmethod
    def _build_capacities(
        vehicles: list[Vehicle],
    ) -> list[int]:

        capacities = []

        for vehicle in vehicles:

            if vehicle.max_weight_kg is None:
                raise ValueError(
                    f"Vehicle {vehicle.vehicle_id} "
                    "has no max_weight_kg."
                )

            capacities.append(
                int(vehicle.max_weight_kg)
            )

        return capacities

    # ================================================================
    # DEMANDS
    # ================================================================

    @staticmethod
    def _build_demands(
        orders,
        locations: list[RoutingLocation],
    ) -> list[int]:
        """
        Pickup = positive demand.
        Delivery = negative demand.

        Example:

            vehicle 0
            pickup A  +500
            delivery A -500
        """

        order_lookup = {
            order.order_id: order
            for order in orders
        }

        demands: list[int] = []

        for location in locations:

            # Vehicle start/end locations have zero demand.
            if location.kind == "vehicle":

                demands.append(0)
                continue

            if location.order_id is None:
                raise ValueError(
                    "Non-vehicle routing location "
                    "has no order_id."
                )

            order = order_lookup.get(
                location.order_id
            )

            if order is None:
                raise ValueError(
                    f"Could not find order "
                    f"{location.order_id}."
                )

            weight = int(
                order.weight_kg or 0
            )

            if location.kind == "pickup":

                demands.append(weight)

            elif location.kind == "delivery":

                demands.append(-weight)

            else:

                raise ValueError(
                    f"Unknown routing location kind: "
                    f"{location.kind}"
                )

        return demands

    # ================================================================
    # PICKUP / DELIVERY
    # ================================================================

    def _build_pickup_delivery_pairs(
        self,
        world: WorldState,
        vehicles: list[Vehicle],
        orders,
        locations: list[RoutingLocation],
    ) -> list[PickupDeliveryPair]:
        """
        Build pickup/delivery pairs and convert compatible vehicle IDs
        into the vehicle indices used by THIS OR-Tools problem.

        Example:

            selected vehicles:

                index 0 → VAN-01
                index 1 → VAN-03

            compatibility says:

                compatible = [VAN-03]

            result:

                allowed_vehicles = [1]
        """

        pickups = {}
        deliveries = {}

        for location in locations:

            if location.kind == "pickup":

                pickups[
                    location.order_id
                ] = location.matrix_index

            elif location.kind == "delivery":

                deliveries[
                    location.order_id
                ] = location.matrix_index

        # ------------------------------------------------------------
        # Vehicle ID → local OR-Tools index
        # ------------------------------------------------------------

        vehicle_indices = {
            vehicle.vehicle_id: index
            for index, vehicle in enumerate(
                vehicles
            )
        }

        pairs = []

        for order in orders:

            compatibility = (
                world.compatibility_results.get(
                    order.order_id
                )
            )

            if compatibility is None:
                continue

            if (
                compatibility.status
                != CompatibilityStatus.ROUTABLE
            ):
                continue

            pickup_index = pickups.get(
                order.order_id
            )

            delivery_index = deliveries.get(
                order.order_id
            )

            if pickup_index is None:
                raise ValueError(
                    f"No pickup location found "
                    f"for order {order.order_id}."
                )

            if delivery_index is None:
                raise ValueError(
                    f"No delivery location found "
                    f"for order {order.order_id}."
                )

            # --------------------------------------------------------
            # Convert compatible vehicle IDs to LOCAL indices
            # --------------------------------------------------------

            allowed_vehicle_indices = []

            for compatible_vehicle in (
                compatibility.compatible
            ):

                local_index = vehicle_indices.get(
                    compatible_vehicle.vehicle_id
                )

                if local_index is not None:

                    allowed_vehicle_indices.append(
                        local_index
                    )

            # --------------------------------------------------------
            # No selected vehicle can service this order.
            #
            # This is different from the compatibility agent saying
            # UNSERVICEABLE. It may be that the vehicle became
            # unavailable between compatibility evaluation and
            # problem construction.
            # --------------------------------------------------------

            if not allowed_vehicle_indices:

                continue

            # --------------------------------------------------------
            # Store converted indices in CompatibilityResult too.
            #
            # This makes the result useful to later components.
            # --------------------------------------------------------

            compatibility.allowed_vehicle_indices = (
                allowed_vehicle_indices
            )

            pairs.append(
                PickupDeliveryPair(
                    order_id=order.order_id,
                    pickup=pickup_index,
                    delivery=delivery_index,
                    allowed_vehicles=(
                        allowed_vehicle_indices
                    ),
                )
            )

        return pairs