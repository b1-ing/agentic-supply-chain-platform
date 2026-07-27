from graphs.planning.graph import build_planning_graph
from services.world.world_manager import world_manager


class PlanningWorkflow:
    """
    Executes the complete planning pipeline.

    The workflow is responsible for orchestrating the planning graph.
    Individual planning logic lives inside graph nodes.
    """

    def __init__(self):

        self.graph = build_planning_graph()

    async def run(self):

        world = world_manager.get_world()

        result = await self.graph.ainvoke(world)

        return result