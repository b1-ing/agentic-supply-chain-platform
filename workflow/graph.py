from langgraph.graph import StateGraph, END

from workflow.state import WorkflowState

from workflow.nodes.fetch_node import fetch_node
from workflow.nodes.match_node import match_node
from workflow.nodes.context_node import context_node
from workflow.nodes.planning_node import planning_node
from workflow.nodes.constraint_node import constraint_node
from workflow.nodes.graph_node import graph_node


def build_workflow():

    builder = StateGraph(WorkflowState)

    builder.add_node("fetch", fetch_node)
    builder.add_node("match", match_node)
    builder.add_node("context", context_node)
    builder.add_node("planning", planning_node)

    builder.set_entry_point("fetch")

    builder.add_edge("fetch", "match")
    builder.add_edge("match", "context")
    builder.add_edge("context", "planning")
    builder.add_edge("planning", END)

    return builder.compile()