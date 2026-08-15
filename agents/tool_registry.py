# agent/tool_registry.py

from agents.tools.world_tools import get_world_state
from agents.tools.order_tools import create_order, assess_order, evaluate_compatibility, delete_order, modify_order, modify_active_order, cancel_active_order
from agents.tools.routing_tools import plan_routes, route_between_places, decide_routing_strategy, simple_fleet_route
from agents.tools.geocoding_tools import geocode_location, geocode_order
from agents.tools.traffic_tools import get_traffic_incidents,report_traffic_incident, find_affected_routes,reroute_affected_routes

TOOLS = {
    "get_world_state": get_world_state,
    "create_order": create_order,
    "plan_routes": plan_routes,
    "assess_order": assess_order,
    "decide_routing_strategy": decide_routing_strategy,
    "route_between_places": route_between_places,
    "geocode_location": geocode_location,
    "evaluate_compatibility": evaluate_compatibility,
    "geocode_order": geocode_order,
    "simple_fleet_route": simple_fleet_route,
    "delete_order": delete_order,
    "modify_order": modify_order,
    "get_traffic_incidents": get_traffic_incidents,
    "report_traffic_incident": report_traffic_incident,
    "find_affected_routes": find_affected_routes,
    "reroute_affected_routes": reroute_affected_routes,
    "modify_active_order": modify_active_order,
    "cancel_active_order": cancel_active_order

}