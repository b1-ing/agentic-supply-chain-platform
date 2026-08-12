import asyncio

import uvicorn

from app.runtime import Runtime
from app.initialise import initialise_world


async def main():

    ############################################################
    # Initialise shared world
    ############################################################

    initialise_world()

    ############################################################
    # API
    ############################################################

    api_config = uvicorn.Config(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
    )

    server = uvicorn.Server(api_config)

    ############################################################
    # Runtime
    ############################################################

    runtime = Runtime()

    ############################################################
    # Run both against the SAME WorldManager
    ############################################################

    await asyncio.gather(
        runtime.run(),
        server.serve(),
    )


if __name__ == "__main__":
    asyncio.run(main())
