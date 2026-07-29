# services/traffic/traffic_pipeline.py


from services.traffic.road_matcher import RoadMatcher
from graphs.traffic.graph import TrafficGraphService
from services.world.world_manager import world_manager
from services.lta_service import LTADataMallClient

from ingestion.traffic_incidents import TrafficIncidentService
from ingestion.speed_bands import SpeedBandService
# from ingestion.lta.roadworks import RoadworksService

class TrafficPipeline:
    """
    Complete traffic ingestion pipeline.

    Responsibilities
    ----------------
    1. Download live traffic information.
    2. Match events onto the road graph.
    3. Update graph edge travel times / penalties.
    4. Store the latest traffic state in WorldState.

    This class should be called periodically
    (e.g. every 30-60 seconds).
    """

    def __init__(self):
        client = LTADataMallClient()
        self.incident_service = TrafficIncidentService(client=client)
        self.speed_band_service = SpeedBandService(client=client)
        # self.roadworks_service = RoadworksService()

        self.matcher = RoadMatcher()
        self.graph_service = TrafficGraphService()

    ####################################################################
    # Main update
    ####################################################################

    def update(self):

        world = world_manager.get_world()

        ###############################################################
        # Fetch latest LTA data
        ###############################################################

        incidents = self.incident_service.fetch()

        speed_bands = self.speed_band_service.fetch()

        # roadworks = self.roadworks_service.fetch()

        ###############################################################
        # Match onto graph
        ###############################################################

        matched_incidents = self.matcher.match_incidents(
            world.graph,
            incidents,
        )

        matched_speed_bands = self.matcher.match_speed_bands(
            world.graph,
            speed_bands,
        )

        # matched_roadworks = self.matcher.match_roadworks(
        #     world.graph,
        #     roadworks,
        # )

        ###############################################################
        # Apply graph updates
        ###############################################################

        self.graph_service.update(
            world=world,
            speed_bands=matched_speed_bands,
            incidents=matched_incidents,
            # matched_roadworks=matched_roadworks,
        )

        ###############################################################
        # Update WorldState
        ###############################################################

        world.traffic_events = incidents
        world.matched_events = (
                matched_incidents
                + matched_speed_bands
                + matched_roadworks
        )

        return world