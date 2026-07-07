import asyncio
import time

from services.lta_service import LTATrafficService, LTADataMallClient


class TrafficAgent:
    def __init__(self, world, update_interval=60):
        self.world = world
        self.update_interval = update_interval

        self.cache_path = "cache/lta_osm_mapping.json"

        self.client = LTADataMallClient()
        self.lta = LTATrafficService(self.client)

    async def run(self):

        print("[TrafficAgent] Starting...")

        while True:
            start = time.perf_counter()

            await self.sync_traffic()

            elapsed = time.perf_counter() - start

            print(f"[TrafficAgent] Traffic update completed in {elapsed:.2f}s")

            await asyncio.sleep(max(0, self.update_interval - elapsed))

    async def sync_traffic(self):

        self.world.graph = await self.lta.sync_network_flow_async(
            self.world.graph,
            self.cache_path,
        )

        self.world.traffic_timestamp = time.time()

        # Later:
        # await self.world.event_queue.put(TrafficUpdated())
