# services/routing/compatibility_service.py

from dataclasses import dataclass

from models.world.world_state import WorldState
from models.order.incoming_order import IncomingOrder
from models.vehicles.vehicle import Vehicle, VehicleStatus
from models.routing.compatible_vehicle import CompatibleVehicle
from models.routing.incompatible_vehicle import IncompatibleVehicle
from models.routing.compatibility_result import CompatibilityResult, CompatibilityStatus

import networkx as nx


class CompatibilityService:
    def evaluate(
        self,
        world: WorldState,
        order: IncomingOrder,
    ) -> CompatibilityResult:

        compatible = []
        incompatible = []

        for vehicle in world.vehicles:
            reason = self._failure_reason(
                vehicle,
                order,
            )

            if reason is None:
                compatible.append(
                    CompatibleVehicle(
                        vehicle_id=vehicle.vehicle_id,
                        status=vehicle.status.value,
                        current_node=vehicle.current_node,
                        remaining_capacity_kg=self._remaining_capacity(
                            vehicle,
                        ),
                        remaining_route_minutes=self._remaining_route_minutes(
                            world,
                            vehicle,
                        ),
                        distance_to_pickup_minutes=self._distance_to_pickup(
                            world,
                            vehicle,
                            order,
                        ),
                    )
                )

            else:
                incompatible.append(
                    IncompatibleVehicle(
                        vehicle_id=vehicle.vehicle_id,
                        reason=reason,
                    )
                )

        idle = [v for v in compatible if v.status == VehicleStatus.IDLE.value]

        if idle:
            status = CompatibilityStatus.ROUTABLE
        elif compatible:
            status = CompatibilityStatus.WAITING
        else:
            status = CompatibilityStatus.UNSERVICEABLE

        allowed_vehicle_indices = [
            i
            for i, vehicle in enumerate(world.vehicles)
            if self._failure_reason(vehicle, order) is None
            and vehicle.status == VehicleStatus.IDLE
        ]

        return CompatibilityResult(
            order_id=order.order_id,
            status=status,
            allowed_vehicle_indices=allowed_vehicle_indices,
            compatible=compatible,
            incompatible=incompatible,
        )

    ####################################################################
    # Constraint checking
    ####################################################################

    def _failure_reason(
        self,
        vehicle: Vehicle,
        order: IncomingOrder,
    ) -> str | None:

        if order.refrigerated and not vehicle.refrigerated:
            return "Vehicle is not refrigerated."

        if order.height_m and order.height_m > vehicle.height_m:
            return (
                f"Order height ({order.height_m}m) "
                f"exceeds vehicle height ({vehicle.height_m}m)."
            )

        if order.weight_kg and order.weight_kg > vehicle.max_weight_kg:
            return (
                f"Order weight ({order.weight_kg}kg) "
                f"exceeds vehicle capacity ({vehicle.max_weight_kg}kg)."
            )

        if order.hazardous and not vehicle.hazardous_certified:
            return "Vehicle is not hazardous-certified."

        return None

    ####################################################################
    # Operational information
    ####################################################################

    def _remaining_capacity(
        self,
        vehicle: Vehicle,
    ) -> float:

        return getattr(
            vehicle,
            "remaining_capacity_kg",
            vehicle.max_weight_kg,
        )

    def _remaining_route_minutes(
        self,
        world: WorldState,
        vehicle: Vehicle,
    ) -> float:

        route = next(
            (r for r in world.routes if r.vehicle_id == vehicle.vehicle_id),
            None,
        )

        if route is None:
            return 0.0

        elapsed = getattr(
            vehicle,
            "elapsed_route_seconds",
            0,
        )

        remaining = max(
            route.total_travel_time - elapsed,
            0,
        )

        return remaining / 60

    def _distance_to_pickup(
        self,
        world: WorldState,
        vehicle: Vehicle,
        order: IncomingOrder,
    ) -> float | None:

        if vehicle.current_node is None or order.pickup_node is None:
            return None

        try:
            travel_time = nx.shortest_path_length(
                world.graph,
                source=vehicle.current_node,
                target=order.pickup_node,
                weight="travel_time",
            )

            return travel_time / 60

        except nx.NetworkXNoPath:
            return None
