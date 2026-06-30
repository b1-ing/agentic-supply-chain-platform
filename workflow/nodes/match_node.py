# workflow/nodes/match_node.py

from services.road_matcher import RoadMatcher
from langsmith import traceable


@traceable(name="Road Matcher")
def match_node(state):

    world = state["world"]

    matcher = RoadMatcher(world.graph)

    matched = []

    for incident in world.traffic_events:
        edges = matcher.nearby_edges(incident.latitude, incident.longitude)

        matched.append({"incident": incident, "edges": edges})

    world.matched_events = matched

    return {"world": world}
