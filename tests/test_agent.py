import asyncio

from app.initialise import initialise_world
from agents.operations_agent import OperationsAgent


async def main():

    # Initialise the shared world first
    initialise_world()

    agent = OperationsAgent()

    result = await agent.run(
        "Create an order to deliver 500kg of cold goods from DSTA to Changi Airport."
    )

    print("\nAGENT:")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())