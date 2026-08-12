# agent/tools/world_tools.py

from services.world.world_manager import world_manager


def get_world_state():
    world = world_manager.get_world()

    return {
        "vehicles": [
            {
                "vehicle_id": v.vehicle_id,
                "status": v.status,
                "current_node": v.current_node,
                "current_route_id": v.current_route_id,
            }
            for v in world.vehicles
        ],
        "orders": [
            {
                "order_id": o.order_id,
                "pickup_address": o.pickup_address,
                "delivery_address": o.delivery_address,
                "assigned_vehicle": o.assigned_vehicle,
            }
            for o in (
                    list(world.new_orders)
                    + list(world.orders_in_progress)
                    + list(world.unserviceable_orders)
            )
        ],
        "routes": [
            {
                "route_id": r.route_id,
                "vehicle_id": r.vehicle_id,
                "total_distance": r.total_distance,
                "total_travel_time": r.total_travel_time,
            }
            for r in world.routes
        ],
    }