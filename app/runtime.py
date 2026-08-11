import time

from app.initialise import initialise_world

from services.order.order_service import OrderService
from services.traffic.traffic_pipeline import TrafficPipeline
import asyncio

class Runtime:

    def __init__(self):

        self.order_service = OrderService()

        self.traffic_pipeline = TrafficPipeline()

    async def run(self):

        while True:

            prompt = await asyncio.to_thread(
                    input,
                    "> ",
                )

            prompt = prompt.strip()

            if not prompt:
                continue

            result = await self.order_service.process_order(prompt)


            print(
                result["decision"]
            )

            world = result["world"]

            print(
                f"\nPending orders     : "
                f"{len(world.new_orders)}"
            )

            print(
                f"In-progress orders : "
                f"{len(world.orders_in_progress)}"
            )

            print(
                f"Vehicle routes     : "
                f"{len(world.routes)}"
            )

            time.sleep(1)