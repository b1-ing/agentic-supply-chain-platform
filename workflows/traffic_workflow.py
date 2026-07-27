from graphs.traffic.graph import build_traffic_graph
from services.world.world_manager import world_manager


class TrafficWorkflow:
    """
    Executes the complete traffic update pipeline.

    Responsibilities
    ----------------
    - ingest live traffic
    - analyse incidents
    - match incidents onto the graph
    - update graph penalties
    - update WorldState
    """

    def __init__(self):

        self.graph = build_traffic_graph()

    async def run(self):

        world = world_manager.get_world()

        result = await self.graph.ainvoke(world)

        return result
