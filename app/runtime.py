import time

from app.initialise import initialise_world

from services.traffic.traffic_pipeline import TrafficPipeline
from services.simulation.vehicle_simulator import (
    VehicleSimulationService,
)
import asyncio
from services.world.world_manager import world_manager


class Runtime:
    def __init__(self):


        self.traffic_pipeline = TrafficPipeline()

        self.vehicle_simulator = (
            VehicleSimulationService()
        )

    async def run(self):

#         last_tick = time.monotonic()

        while True:

#             now = time.monotonic()
#
#             dt = now - last_tick
#             last_tick = now
#
#             world = world_manager.get_world()
#
#             self.vehicle_simulator.update(
#                 world,
#                 dt,
#             )


            # print(f"\nPending orders     : {len(world.new_orders)}")
            #
            # print(f"In-progress orders : {len(world.orders_in_progress)}")
            #
            # print(f"Vehicle routes     : {len(world.routes)}")

            await asyncio.sleep(1)
