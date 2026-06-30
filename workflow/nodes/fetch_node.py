# workflow/nodes/fetch_node.py

from services.traffic_service import TrafficService
from services.lta_service import LTADataMallClient
from langsmith import traceable

# @traceable(name="Fetch Traffic")
def fetch_node(state):

    world = state["world"]

    client = LTADataMallClient()
    traffic_service = TrafficService(client)

    world.traffic_events = traffic_service.fetch_live_incidents()

    return {"world": world}
