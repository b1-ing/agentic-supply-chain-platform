# services/traffic/traffic_ingestion_service.py

from services.traffic.traffic_incident_matcher import TrafficIncidentMatcher
from services.traffic.graph_update_service import GraphUpdateService

from services.world.world_manager import world_manager

from agents.traffic_analysis_agent import TrafficAnalysisAgent

# Replace these with your own connectors
from services.external.lta_service import LTAService
from services.external.tomtom_service import TomTomService


class TrafficIngestionService:
    """
    End-to-end traffic ingestion pipeline.

    Pipeline

        LTA
            +
        TomTom
            +
        Web

            ↓

        TrafficAnalysisAgent

            ↓

        TrafficIncidentMatcher

            ↓

        GraphUpdateService

            ↓

        WorldState
    """

    def __init__(self):

        self.lta = LTAService()
        self.tomtom = TomTomService()

        self.analysis_agent = TrafficAnalysisAgent()

        self.matcher = TrafficIncidentMatcher()

        self.graph_updater = GraphUpdateService()

    ####################################################################
    # Public
    ####################################################################

    async def run(self):

        world = world_manager.get_world()

        ###############################################################
        # Fetch latest incidents
        ###############################################################

        incidents = []

        incidents.extend(
            self.lta.fetch_incidents()
        )

        incidents.extend(
            self.tomtom.fetch_incidents()
        )

        ###############################################################
        # Analyse incidents
        ###############################################################

        analysed_incidents = []

        for incident in incidents:

            analysed = await self.analysis_agent.run(
                incident
            )

            analysed_incidents.append(
                analysed
            )

        ###############################################################
        # Match onto graph
        ###############################################################

        matched = []

        for incident in analysed_incidents:

            matched.append(
                self.matcher.match(
                    world.graph,
                    incident,
                )
            )

        ###############################################################
        # Apply penalties
        ###############################################################

        graph = self.graph_updater.update(
            world.graph,
            matched,
        )

        ###############################################################
        # Store into WorldState
        ###############################################################

        world.graph = graph
        world.traffic_events = analysed_incidents
        world.matched_events = matched

        return world