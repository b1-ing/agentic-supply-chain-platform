from fastapi import APIRouter, Depends, HTTPException

from models.world.world_state import WorldState
from models.order.incoming_order import IncomingOrder
from pydantic import BaseModel
from api.dependencies import get_world
from api.schemas.order import OrderResponse
from services.world.world_manager import world_manager
from shapely.geometry import LineString


router = APIRouter(
    prefix="/api/orders",
    tags=["orders"],
)


def serialize_geometry(geometry):
    if geometry is None:
        return None

    if isinstance(geometry, LineString):
        return [
            [float(lon), float(lat)]
            for lon, lat in geometry.coords
        ]

    return geometry


class OrderPromptRequest(BaseModel):
    prompt: str



def serialize_order(order) -> IncomingOrder:

    return IncomingOrder(
        order_id=order.order_id,
        pickup_address=order.pickup_address,
        delivery_address=order.delivery_address,
        pickup_lat=order.pickup_lat,
        pickup_lon=order.pickup_lon,
        delivery_lat=order.delivery_lat,
        delivery_lon=order.delivery_lon,
        pickup_node=order.pickup_node,
        delivery_node=order.delivery_node,
        height_m=order.height_m,
        weight_kg=order.weight_kg,
        refrigerated=order.refrigerated,
        hazardous=order.hazardous,
        fragile=order.fragile,
        oversized=order.oversized,
        earliest_pickup=(
            str(order.earliest_pickup) if order.earliest_pickup is not None else None
        ),
        latest_pickup=(
            str(order.latest_pickup) if order.latest_pickup is not None else None
        ),
        earliest_delivery=(
            str(order.earliest_delivery)
            if order.earliest_delivery is not None
            else None
        ),
        latest_delivery=(
            str(order.latest_delivery) if order.latest_delivery is not None else None
        ),
        assigned_vehicle=order.assigned_vehicle,
        notes=order.notes,
    )


def all_orders(world: WorldState):

    return (
        list(world.new_orders)
        + list(world.orders_in_progress)
        + list(world.cancelled_orders)
        + list(world.unserviceable_orders)
    )


@router.get(
    "",
    response_model=list[IncomingOrder],
)
def get_orders(
    world: WorldState = Depends(get_world),
):

    return [serialize_order(order) for order in all_orders(world)]


@router.get(
    "/new",
    response_model=list[IncomingOrder],
)
def get_new_orders(
    world: WorldState = Depends(get_world),
):

    return [serialize_order(order) for order in world.new_orders]


@router.get(
    "/in-progress",
    response_model=list[IncomingOrder],
)
def get_in_progress_orders(
    world: WorldState = Depends(get_world),
):

    return [serialize_order(order) for order in world.orders_in_progress]


@router.get(
    "/cancelled",
    response_model=list[OrderResponse],
)
def get_cancelled_orders(
    world: WorldState = Depends(get_world),
):

    return [serialize_order(order) for order in world.cancelled_orders]


@router.get(
    "/unserviceable",
    response_model=list[IncomingOrder],
)
def get_unserviceable_orders(
    world: WorldState = Depends(get_world),
):

    return [serialize_order(order) for order in world.unserviceable_orders]


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
)
def get_order(
    order_id: str,
    world: WorldState = Depends(get_world),
):

    order = next(
        (order for order in all_orders(world) if order.order_id == order_id),
        None,
    )

    if order is None:
        raise HTTPException(
            status_code=404,
            detail=f"Order {order_id} not found",
        )

    return serialize_order(order)


@router.post("")
async def create_order(
    request: OrderPromptRequest,
):

    result = await order_service.process_order(request.prompt)

    return result
