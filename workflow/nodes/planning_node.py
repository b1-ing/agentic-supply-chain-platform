from agents.planning_agent import PlanningAgent
from langsmith import traceable

agent = PlanningAgent()

# @traceable(name="Planning Agent")
def planning_node(state):

    world = state["world"]

    result = agent.evaluate(world.context)

    world.assessments = result.severity

    world.recommend_replan = result.recommend_replan
    world.summary = result.road_status

    print(world)

    return {"world": world}