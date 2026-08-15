from fastapi import APIRouter, Depends

from models.world.world_state import WorldState

from api.dependencies import get_world
from api.schemas.world import (
    WorldResponse,
    WorldSummaryResponse,
)

from api.routes.vehicles import serialize_vehicle
from api.routes.orders import serialize_order
from api.routes.routes import serialize_route
from api.routes.depots import serialize_depot


router = APIRouter(
    prefix="/api/world",
    tags=["world"],
)


@router.get(
    "",
    response_model=WorldResponse,
)
def get_world(
    world: WorldState = Depends(get_world),


):

    return WorldResponse(
        summary=WorldSummaryResponse(
            vehicle_count=len(world.vehicles),
            route_count=len(world.routes),
            depot_count=len(world.depots),
            new_order_count=len(world.new_orders),
            in_progress_order_count=len(world.orders_in_progress),
            cancelled_order_count=len(world.cancelled_orders),
            unserviceable_order_count=len(world.unserviceable_orders),
            traffic_event_count=len(world.traffic_events),
        ),
        vehicles=[serialize_vehicle(vehicle) for vehicle in world.vehicles],
        depots=[serialize_depot(depot) for depot in world.depots],
        new_orders=[serialize_order(order) for order in world.new_orders],
        orders_in_progress=[
            serialize_order(order) for order in world.orders_in_progress
        ],
        cancelled_orders=[serialize_order(order) for order in world.cancelled_orders],
        unserviceable_orders=[
            serialize_order(order) for order in world.unserviceable_orders
        ],
        routes=[serialize_route(route) for route in world.routes],
    )
