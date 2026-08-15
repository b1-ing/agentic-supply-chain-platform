# agent/operations_agent.py

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
REQUEST TYPES
============================================================

There are two fundamentally different types of requests.

------------------------------------------------------------
A. READ-ONLY ROUTE REQUEST
------------------------------------------------------------

Examples:

"What's the fastest route from Bukit Timah Plaza to Clementi Mall?"

"Find a route from A to B avoiding PIE."

"How do I get from X to Y?"

For these requests:

1. Use route_between_places.
2. Do NOT create an operational order.
3. Do NOT assign a vehicle.
4. Do NOT modify WorldState.

Return the calculated route.

------------------------------------------------------------
B. OPERATIONAL LOGISTICS REQUEST
------------------------------------------------------------

Examples:

"Deliver 10kg of cold fish from Bukit Timah Plaza to Clementi Mall."

"Send this order from A to B."

"Transport 500kg of goods from X to Y."

"Deliver this refrigerated shipment while avoiding PIE."

For these requests, the user is asking the system to
perform an operational logistics action.

You MUST execute the operational workflow:

1. assess_order
2. create_order
3. evaluate compatibility
4. plan fleet routes
5. return the resulting operational state

Do NOT stop after finding a point-to-point route.

The route_between_places tool may be used as supporting
information, but it is NOT a substitute for fleet routing.

============================================================
OPERATIONAL WORKFLOW
============================================================

For an operational logistics request:

Step 1:
Call assess_order to interpret the natural-language request.

Step 2:
If the assessment contains enough information to create
the order, call create_order. Afterward, call geocode_order.

Step 3:
Evaluate vehicle compatibility.

Step 4:
If the order is serviceable, call the fleet routing tool.

Step 5:
The fleet routing result should update WorldState with:
- the order status
- vehicle assignment
- vehicle route
- route information

Step 6:
Return the actual order ID, assigned vehicle, and route
information to the user.

Never claim that an order was created, assigned, or routed
unless the corresponding tool actually succeeded.

============================================================
ROUTING STRATEGY
============================================================

Do not automatically call plan_routes for every delivery.

After creating an operational order and evaluating compatibility,
call decide_routing_strategy.

If strategy is SIMPLE:

1. Call simple_fleet_route.
2. Do NOT call route_between_places as the final operational action.
3. simple_fleet_route MUST:
   - select a compatible vehicle
   - apply routing constraints
   - construct the route
   - assign the vehicle
   - persist the VehicleRoute
   - update the order
   - update WorldState

route_between_places is read-only and must not be used
as a substitute for simple fleet routing.

If the strategy is CVRP:

- Call plan_routes.
- Use the fleet-wide optimisation pipeline.
- Consider all relevant routable orders and vehicles.

The routing strategy decision determines whether OR-Tools/CVRP
is necessary.

============================================================
IMPORTANT
============================================================

"route from A to B"
means READ-ONLY routing.

"deliver/transport/send/dispatch X from A to B"
means OPERATIONAL execution.

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