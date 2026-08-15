from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
import json
from fastapi.responses import StreamingResponse
from agents.operations_agent import OperationsAgent


router = APIRouter(
    prefix="/api/agent",
    tags=["agent"],
)


class AgentRequest(BaseModel):
    message: str


class AgentResponse(BaseModel):
    response: str


agent = OperationsAgent()


@router.post("")
async def run_agent(request: AgentRequest):

    queue = asyncio.Queue()

    async def emit(event):
        await queue.put(event)

    async def run_agent_task():
        try:
            result = await agent.run(
                request.message,
                emit=emit,
            )

            await queue.put({
                "type": "agent_final",
                "output": str(result),
            })

        except Exception as exc:
            await queue.put({
                "type": "agent_error",
                "error": str(exc),
            })

        finally:
            await queue.put(None)

    task = asyncio.create_task(
        run_agent_task()
    )

    async def event_stream():

        while True:

            event = await queue.get()

            if event is None:
                break

            yield (
                f"data: "
                f"{json.dumps(event, default=str)}"
                f"\n\n"
            )

        await task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )