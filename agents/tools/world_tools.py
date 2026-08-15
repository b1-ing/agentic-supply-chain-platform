# agent/tools/world_tools.py

from services.world.world_manager import world_manager
from api.routes.world import WorldResponse, WorldSummaryResponse
from api.routes.vehicles import serialize_vehicle
from api.routes.depots import serialize_depot
from api.routes.routes import serialize_route
from api.routes.traffic import serialize_traffic_incident
from api.schemas.world import (
    WorldResponse,
    WorldSummaryResponse,
)


def serialize_world(world) -> WorldResponse:
    return WorldResponse(
        summary=WorldSummaryResponse(
            vehicle_count=len(world.vehicles),
            route_count=len(world.routes),
            new_order_count=len(world.new_orders),
            in_progress_order_count=len(world.orders_in_progress),
            cancelled_order_count=len(world.cancelled_orders),
            unserviceable_order_count=len(world.unserviceable_orders),
            traffic_event_count=len(world.traffic_events),
        ),



        vehicles=[
            serialize_vehicle(vehicle)
            for vehicle in world.vehicles
        ],

        depots=[
            serialize_depot(depot)
            for depot in world.depots
        ],

        traffic_events=[
            serialize_traffic_incident(incident)
            for incident in world.traffic_events
        ],

        new_orders=list(world.new_orders),

        orders_in_progress=list(world.orders_in_progress),

        cancelled_orders=list(world.cancelled_orders),

        unserviceable_orders=list(world.unserviceable_orders),

        routes=[
            serialize_route(route)
            for route in world.routes
        ],
    )



def get_world_state():
    world = world_manager.get_world()

    return serialize_world(world)