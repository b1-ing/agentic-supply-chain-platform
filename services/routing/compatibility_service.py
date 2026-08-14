from agents.compatibility_agent import CompatibilityAgent


class CompatibilityService:

    def __init__(self):
        self.agent = CompatibilityAgent()

    async def evaluate(
        self,
        order_id: str,
    ) -> dict:

        return await self.agent.evaluate(
            order_id,
        )