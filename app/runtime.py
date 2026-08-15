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

        # Traffic refresh interval
        self.traffic_update_interval = 5 * 60  # 5 minutes

    async def run(self):

        last_tick = time.monotonic()

        # Separate timer for traffic updates
        last_traffic_update = time.monotonic()

        print("[RUNTIME] Simulation started.")

        self.traffic_pipeline.update()

        last_traffic_update = time.monotonic()

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
            # Update traffic every 5 minutes
            # --------------------------------------------------

            if now - last_traffic_update >= self.traffic_update_interval:

                print("[RUNTIME] Updating traffic...")

                self.traffic_pipeline.update()

                last_traffic_update = now

            # --------------------------------------------------
            # Advance vehicle simulation
            # --------------------------------------------------

            self.vehicle_simulator.update(
                world=world,
                dt_seconds=dt,
            )

            # --------------------------------------------------
            # Tick rate
            # --------------------------------------------------

            await asyncio.sleep(1)