from fastapi import APIRouter, Depends, HTTPException

from models.world.world_state import WorldState

from api.dependencies import get_world
from api.schemas.vehicle import VehicleResponse


router = APIRouter(
    prefix="/api/vehicles",
    tags=["vehicles"],
)


def serialize_vehicle(vehicle) -> VehicleResponse:

    return VehicleResponse(
        vehicle_id=vehicle.vehicle_id,
        status=vehicle.status,
        current_node=vehicle.current_node,
        current_lat=vehicle.current_lat,
        current_lon=vehicle.current_lon,
        max_weight_kg=vehicle.max_weight_kg,
        height_m=vehicle.height_m,
        width_m=vehicle.width_m,
        length_m=vehicle.length_m,
        refrigerated=vehicle.refrigerated,
        hazardous_certified=vehicle.hazardous_certified,
        current_route_id=None,
    )


@router.get(
    "",
    response_model=list[VehicleResponse],
)
def get_vehicles(
    world: WorldState = Depends(get_world),
):

    return [serialize_vehicle(vehicle) for vehicle in world.vehicles]


@router.get(
    "/{vehicle_id}",
    response_model=VehicleResponse,
)
def get_vehicle(
    vehicle_id: str,
    world: WorldState = Depends(get_world),
):

    vehicle = next(
        (v for v in world.vehicles if v.vehicle_id == vehicle_id),
        None,
    )

    if vehicle is None:
        raise HTTPException(
            status_code=404,
            detail=f"Vehicle {vehicle_id} not found",
        )

    return serialize_vehicle(vehicle)
