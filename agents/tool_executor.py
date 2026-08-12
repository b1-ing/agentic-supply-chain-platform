# agent/tool_executor.py

from agents.tool_registry import TOOLS


async def execute_tool(name: str, arguments: dict):

    tool = TOOLS.get(name)

    if tool is None:
        raise ValueError(f"Unknown tool: {name}")

    result = tool(**arguments)

    if hasattr(result, "__await__"):
        result = await result

    return result