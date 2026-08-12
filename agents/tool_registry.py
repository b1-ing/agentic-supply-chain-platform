# agent/tool_registry.py

from agents.tools.world_tools import get_world_state
from agents.tools.order_tools import create_order
from agents.tools.routing_tools import plan_routes


TOOLS = {
    "get_world_state": get_world_state,
    "create_order": create_order,
    "plan_routes": plan_routes,
}