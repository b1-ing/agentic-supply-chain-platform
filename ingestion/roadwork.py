from datetime import datetime

from services.lta_service import LTADataMallClient
# from models.events import Roadwork
###     WIP     ###

class RoadworksService:

    def __init__(self, client: LTADataMallClient):
        self.client = client

    def fetch(self) -> list[Roadwork]:

        raw = self.client.fetch_all_pages("RoadWorks")

        roadworks = []

        for item in raw:

            roadworks.append(
                Roadwork(
                    ...
                )
            )

        return roadworks