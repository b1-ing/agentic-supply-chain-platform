# agent/operations_agent.py
"""
Operations Agent for the agentic supply-chain control tower.

This module defines the agent responsible for interpreting natural-language
operational requests and orchestrating the appropriate deterministic services.

The Operations Agent acts as the decision and coordination layer between the
user and the operational WorldState. It determines what needs to happen and
selects the appropriate tools, while domain services remain responsible for
performing the actual operational computations and state mutations.

The agent may orchestrate operations such as:

    - assessing natural-language orders
    - creating orders
    - resolving and geocoding locations
    - evaluating vehicle compatibility
    - selecting a routing strategy
    - planning routes
    - observing the current operational world
    - modifying active orders
    - responding to operational disruptions

The agent does not directly perform deterministic routing, vehicle
compatibility calculations, graph optimisation, or geospatial processing.
Those responsibilities are delegated to the appropriate services and tools.

The intended execution model is:

    User request
        |
        v
    Operations Agent
        |
        v
    Tool selection / orchestration
        |
        v
    Deterministic services
        |
        v
    WorldState
        |
        v
    Agent observes updated state
        |
        v
    Final response

The WorldState remains the authoritative source of operational truth.
Agent reasoning, intermediate tool results, and trace information must not
be treated as independent sources of truth.

The agent therefore follows the broader control-tower loop:

    Observe -> Assess -> Plan -> Execute -> Observe again

This separation allows the LLM to provide flexible natural-language
reasoning and orchestration while keeping operational decisions such as
routing, compatibility, constraint enforcement, and fleet optimisation
deterministic and reproducible.
"""

from openai import AsyncOpenAI

from agents.tool_registry import TOOLS
from agents.tool_schemas import TOOLS_SCHEMA
from agents.tool_executor import execute_tool
import json
import time
import uuid

SYSTEM_PROMPT = """
You are the operations agent for an agentic supply-chain system.

You have access to tools for:
- assessing orders
- creating orders
- checking vehicle compatibility
- routing
- reading and modifying the operational world



============================================================
IMPORTANT
============================================================

When the user explicitly asks to deliver or transport cargo,
do not merely provide directions.
"""

async def emit_event(emit, event):
    if emit is not None:
        await emit(event)



class OperationsAgent:

    def __init__(self):
        self.client = AsyncOpenAI()

    async def run(self, user_message: str, emit=None):

        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]

        while True:

            response = await self.client.chat.completions.create(
                model="gpt-5.4",
                messages=messages,
                tools=TOOLS_SCHEMA,
                tool_choice="auto",
            )

            message = response.choices[0].message

            # GPT is finished
            if not message.tool_calls:
                return message.content

            # Preserve GPT's tool-call message
            # this is to emit the agent's tool-calls to the /agents api which
            # will then display these on the front end for visibility
            messages.append(message)

            for tool_call in message.tool_calls:

                name = tool_call.function.name

                arguments = json.loads(
                    tool_call.function.arguments
                )

                trace_id = str(uuid.uuid4())
                started = time.perf_counter()

                print(f"[AGENT] Calling {name}({arguments})")

                await emit_event(
                    emit,
                    {
                        "type": "tool_start",
                        "id": trace_id,
                        "toolName": name,
                        "args": arguments,
                    },
                )

                try:

                    result = await execute_tool(
                        name,
                        arguments,
                    )

                    duration_ms = (
                        time.perf_counter() - started
                    ) * 1000

                    print(f"[AGENT] Result: {result}")

                    await emit_event(
                        emit,
                        {
                            "type": "tool_end",
                            "id": trace_id,
                            "toolName": name,
                            "status": "completed",
                            "durationMs": round(duration_ms, 2),
                            "result": result,
                        },
                    )

                except Exception as exc:

                    duration_ms = (
                        time.perf_counter() - started
                    ) * 1000

                    await emit_event(
                        emit,
                        {
                            "type": "tool_end",
                            "id": trace_id,
                            "toolName": name,
                            "status": "failed",
                            "durationMs": round(duration_ms, 2),
                            "error": str(exc),
                        },
                    )

                    raise

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            result,
                            default=str,
                        ),
                    }
                )