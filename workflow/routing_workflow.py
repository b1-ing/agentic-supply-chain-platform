from services.osm_service import OSMService
from services.traffic_service import TrafficService
from traffic.road_matcher import RoadMatcher

from engine.constraint_engine import ConstraintEngine
from repository.constraint_repository import ConstraintRepository


class RoutingWorkflow:
    def __init__(self):

        self.osm_service = OSMService()
        self.traffic_service = TrafficService()

    def build_constraints(self):

        graph = self.osm_service.load_graph("Singapore")

        raw_data = self.traffic_service.fetch_live_incidents()

        events = self.traffic_service.normalize(raw_data)

        matcher = RoadMatcher(graph)

        engine = ConstraintEngine(matcher)

        repository = ConstraintRepository()

        for event in events:
            constraint = engine.process_event(event)

            if constraint:
                repository.add(constraint)

        return graph, repository
