from fastapi import APIRouter, Depends, HTTPException

from models.world.world_state import WorldState

from api.dependencies import get_world
from api.schemas.route import (
    RouteResponse,
    RoutePointResponse,
    RouteSegmentResponse,
)


router = APIRouter(
    prefix="/api/routes",
    tags=["routes"],
)


def serialize_route(route) -> RouteResponse:

    stops = []

    for stop in route.stops:

        location = stop.location

        stops.append(
            RoutePointResponse(
                sequence=stop.sequence,

                lat=location.lat,
                lon=location.lon,

                kind=location.kind,

                order_id=location.order_id,
                vehicle_id=location.vehicle_id,
            )
        )

    segments = []

    for segment in route.segments:

        segments.append(
            RouteSegmentResponse(
                geometry=[
                    [lat, lon]
                    for lat, lon in segment.geometry
                ],

                distance_m=segment.distance,
                travel_time_seconds=segment.travel_time,
            )
        )

    return RouteResponse(
        vehicle_id=route.vehicle_id,

        stops=stops,

        segments=segments,

        total_distance_m=route.total_distance,
        total_travel_time_seconds=route.total_travel_time,
    )


@router.get(
    "",
    response_model=list[RouteResponse],
)
def get_routes(
        world: WorldState = Depends(get_world),
):

    return [
        serialize_route(route)
        for route in world.routes
    ]


@router.get(
    "/{vehicle_id}",
    response_model=RouteResponse,
)
def get_vehicle_route(
        vehicle_id: str,
        world: WorldState = Depends(get_world),
):

    route = next(
        (
            route
            for route in world.routes
            if route.vehicle_id == vehicle_id
        ),
        None,
    )

    if route is None:
        raise HTTPException(
            status_code=404,
            detail=f"No route found for vehicle {vehicle_id}",
        )

    return serialize_route(route)