from models.order.incoming_order import IncomingOrder
from models.depot import Depot
from pydantic import BaseModel

from .vehicle import VehicleResponse
from .order import OrderResponse
from .route import RouteResponse
from .traffic import TrafficIncidentResponse


class WorldSummaryResponse(BaseModel):
    vehicle_count: int
    route_count: int

    new_order_count: int
    in_progress_order_count: int
    cancelled_order_count: int
    unserviceable_order_count: int

    traffic_event_count: int


class WorldResponse(BaseModel):
    summary: WorldSummaryResponse

    vehicles: list[VehicleResponse]

    traffic_events: list[TrafficIncidentResponse]

    depots: list[Depot]

    new_orders: list[IncomingOrder]
    orders_in_progress: list[IncomingOrder]
    cancelled_orders: list[IncomingOrder]
    unserviceable_orders: list[IncomingOrder]

    routes: list[RouteResponse]
