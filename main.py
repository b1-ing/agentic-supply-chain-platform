from workflow.graph import build_workflow

from models.world_state import WorldState
from services.osm_service import OSMService

osm = OSMService()

graph = osm.load_graph("Singapore")

world = WorldState(
    graph=graph
)

workflow = build_workflow()

result = workflow.invoke({
    "world": world
})

print(result["world"].assessments)