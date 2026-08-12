# agent/tools/routing_tools.py

from services.world.world_manager import world_manager
from services.routing.routing_service import RoutingService

routing_service = RoutingService()


def plan_routes():

    world = world_manager.get_world()

    route_plan = routing_service.plan_routes(world)

    if route_plan is None:
        return {
            "status": "NO_ROUTE",
            "routes": [],
        }

    return {
        "status": "SUCCESS",
        "routes": [
            {
                "route_id": route.route_id,
                "vehicle_id": route.vehicle_id,
                "distance": route.total_distance,
                "travel_time": route.total_travel_time,
                "stops": [
                    {
                        "sequence": stop.sequence,
                        "lat": stop.location.lat,
                        "lon": stop.location.lon,
                    }
                    for stop in route.stops
                ],
            }
            for route in route_plan.routes
        ],
    }