from agents.compatibility_agent import CompatibilityAgent

from models.routing.compatibility_result import (
    CompatibilityResult,
    CompatibilityStatus,
)
from models.routing.compatible_vehicle import CompatibleVehicle
from models.routing.incompatible_vehicle import IncompatibleVehicle


class CompatibilityService:

    def __init__(self):
        self.agent = CompatibilityAgent()

    async def evaluate(
        self,
        world,
        order_id: str,
    ) -> CompatibilityResult:


        #directly calls the compatibility_agent
        result = await self.agent.evaluate(order_id)

        # ---------------------------------------------------------
        # Build compatible vehicles
        # ---------------------------------------------------------

        compatible = []

        for item in result["compatible"]:

            vehicle = next(
                (
                    vehicle
                    for vehicle in world.vehicles
                    if vehicle.vehicle_id == item["vehicle_id"]
                ),
                None,
            )

            if vehicle is None:
                continue

            compatible.append(
                CompatibleVehicle(
                    vehicle_id=vehicle.vehicle_id,
                    status=str(vehicle.status),
                    current_node=vehicle.current_node,
                    remaining_capacity_kg=vehicle.max_weight_kg,
                    remaining_route_minutes=0,
                    distance_to_pickup_minutes=None,
                )
            )

        # ---------------------------------------------------------
        # Build incompatible vehicles
        # ---------------------------------------------------------

        incompatible = [
            IncompatibleVehicle(
                vehicle_id=item["vehicle_id"],
                reason=item["reason"],
            )
            for item in result["incompatible"]
        ]

        # ---------------------------------------------------------
        # Convert vehicle IDs → OR-Tools vehicle indices
        # ---------------------------------------------------------

        compatible_ids = {
            vehicle.vehicle_id
            for vehicle in compatible
        }

        allowed_vehicle_indices = [
            index
            for index, vehicle in enumerate(world.vehicles)
            if vehicle.vehicle_id in compatible_ids
        ]

        # ---------------------------------------------------------
        # Compatibility status
        # ---------------------------------------------------------

        status_string = result["status"]

        if status_string == "UNCERTAIN":
            status = CompatibilityStatus.WAITING
        else:
            status = CompatibilityStatus(status_string)

        # ---------------------------------------------------------
        # Domain result
        # ---------------------------------------------------------

        return CompatibilityResult(
            order_id=order_id,
            compatible=compatible,
            incompatible=incompatible,
            allowed_vehicle_indices=allowed_vehicle_indices,
            status=status,
        )