# workflow/nodes/planning_node.py

from agents.planning_agent import PlanningAgent
from langsmith import traceable

agent = PlanningAgent()


# Un-comment this whenever you want to see visual traces in your LangSmith dashboard!
# @traceable(name="Planning Agent Node")
def planning_node(state):
    world = state["world"]

    result = agent.evaluate(world.context)

    # This works cleanly now because the fields exist on WorldState!
    world.assessments = result.assessments
    world.recommend_replan = result.recommend_replan
    world.summary = result.summary

    return {"world": world}
