from fastapi import APIRouter
from pydantic import BaseModel

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


@router.post("", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    result = await agent.run(request.message)

    return AgentResponse(
        response=str(result)
    )