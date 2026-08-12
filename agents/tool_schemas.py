TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "get_world_state",
            "description": (
                "Get the current operational state of the fleet, "
                "orders, routes and traffic."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_order",
            "description": (
                "Create and process a new logistics order expressed "
                "in natural language."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": "Natural-language logistics order.",
                    }
                },
                "required": ["prompt"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "plan_routes",
            "description": (
                "Plan routes for currently routable orders "
                "using the available fleet and vehicle constraints."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
]