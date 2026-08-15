import time
import asyncio

from app.initialise import initialise_world

from services.traffic.traffic_pipeline import TrafficPipeline
from services.simulation.vehicle_simulator import (
    VehicleSimulationService,
)
from services.world.world_manager import world_manager


class Runtime:

    def __init__(self):

        self.traffic_pipeline = TrafficPipeline()

        self.vehicle_simulator = (
            VehicleSimulationService()
        )

    async def run(self):

        last_tick = time.monotonic()

        print("[RUNTIME] Simulation started.")

        while True:

            # --------------------------------------------------
            # Calculate elapsed simulation time
            # --------------------------------------------------

            now = time.monotonic()

            dt = now - last_tick

            last_tick = now

            # --------------------------------------------------
            # Get current world
            # --------------------------------------------------

            world = world_manager.get_world()

            # --------------------------------------------------
            # Advance vehicle simulation
            # --------------------------------------------------

            self.vehicle_simulator.update(
                world=world,
                dt_seconds=dt,
            )

            # --------------------------------------------------
            # Debug output
            # --------------------------------------------------

            # --------------------------------------------------
            # Tick rate
            # --------------------------------------------------

            await asyncio.sleep(1)