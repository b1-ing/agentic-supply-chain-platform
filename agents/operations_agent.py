# agent/operations_agent.py

from openai import AsyncOpenAI

from agents.tool_registry import TOOLS
from agents.tool_schemas import TOOLS_SCHEMA
from agents.tool_executor import execute_tool
import json

class OperationsAgent:

    def __init__(self):
        self.client = AsyncOpenAI()

    async def run(self, user_message: str):

        messages = [
            {
                "role": "system",
                "content": """
You are an operations planning agent for a logistics fleet.

You can inspect the world, create orders and plan routes.

Never directly invent vehicle positions, routes or order states.
Use tools to inspect and modify the operational state.

Prefer deterministic routing and compatibility services over
reasoning about exact routes yourself.
""",
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

                print(f"[AGENT] Calling {name}({arguments})")

                result = await execute_tool(
                    name,
                    arguments,
                )

                print(f"[AGENT] Result: {result}")

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