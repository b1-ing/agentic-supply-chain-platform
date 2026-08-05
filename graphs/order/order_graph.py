from langgraph.graph import StateGraph, END

from models.order.order_state import OrderState

from graphs.order.nodes.validate_order import validate_order
from graphs.order.nodes.assess_order import assess_order
from graphs.order.nodes.geocode import geocode_order
from graphs.order.nodes.snap_to_graph import snap_to_graph
from graphs.order.nodes.store_order import store_order


def build_order_graph():

    workflow = StateGraph(OrderState)

    workflow.add_node("validate_order", validate_order)
    workflow.add_node("assess_order", assess_order)
    workflow.add_node("geocode", geocode_order)
    workflow.add_node("store_order", store_order)
    workflow.add_node("snap_to_graph", snap_to_graph)

    workflow.set_entry_point("assess_order")

    workflow.add_edge("assess_order", "validate_order")
    workflow.add_edge("validate_order", "geocode")
    workflow.add_edge("geocode", "snap_to_graph")
    workflow.add_edge("snap_to_graph", "store_order")
    workflow.add_edge("store_order", END)

    return workflow.compile()
