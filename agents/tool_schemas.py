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
                "Create an operational order from a completed "
                "order assessment produced by assess_order. "
                "Do not interpret or modify the assessment."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "assessment": {
                        "type": "object",
                        "description": (
                            "The structured order assessment returned "
                            "by assess_order."
                        ),
                        "properties": {
                            "pickup_address": {
                                "type": "string"
                            },
                            "delivery_address": {
                                "type": "string"
                            },
                            "weight_kg": {
                                "type": ["number", "null"]
                            },
                            "volume_m3": {
                                "type": ["number", "null"]
                            },
                            "pallets": {
                                "type": ["integer", "null"]
                            },
                            "refrigerated": {
                                "type": "boolean"
                            },
                            "hazardous": {
                                "type": "boolean"
                            },
                            "fragile": {
                                "type": "boolean"
                            },
                            "oversized": {
                                "type": "boolean"
                            },
                            "height_m": {
                                "type": ["number", "null"]
                            },
                            "earliest_pickup": {
                                "type": ["string", "null"]
                            },
                            "latest_pickup": {
                                "type": ["string", "null"]
                            },
                            "earliest_delivery": {
                                "type": ["string", "null"]
                            },
                            "latest_delivery": {
                                "type": ["string", "null"]
                            },
                            "constraints": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string"
                                        },
                                        "value": {},
                                        "hard": {
                                            "type": "boolean"
                                        },
                                        "reason": {
                                            "type": ["string", "null"]
                                        },
                                    },
                                    "required": [
                                        "type",
                                        "value",
                                        "hard",
                                    ],
                                },
                            },
                            "notes": {
                                "type": ["string", "null"]
                            },
                        },
                        "required": [
                            "pickup_address",
                            "delivery_address",
                            "constraints",
                        ],
                    }
                },
                "required": ["assessment"],
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

    {
        "type": "function",
        "function": {
            "name": "assess_order",
            "description": (
                "Assess a natural-language logistics order. Extract the "
                "pickup and delivery locations, cargo properties, vehicle "
                "requirements, delivery and pickup time constraints, and "
                "infer relevant operational constraints from the user's "
                "request. Identify missing information and ambiguities. "
                "Do not create an order, assign a vehicle, or plan a route."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {
                        "type": "string",
                        "description": (
                            "The user's natural-language logistics order, "
                            "for example: 'Deliver 500kg of refrigerated "
                            "goods from DSTA to Changi Airport by 16:00.'"
                        ),
                    },
                },
                "required": ["prompt"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "route_between_places",
            "description": (
                "Find a point-to-point logistics route between two places. "
                "Use this for simple routing requests that do not require "
                "assigning multiple orders across a fleet. The tool can "
                "apply requested road restrictions and required waypoints."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {
                        "type": "string",
                        "description": (
                            "Starting place or address."
                        ),
                    },
                    "destination": {
                        "type": "string",
                        "description": (
                            "Destination place or address."
                        ),
                    },
                    "avoid_roads": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "description": (
                            "Roads that should be avoided."
                        ),
                    },
                    "avoid_areas": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "description": (
                            "Named areas that should be avoided."
                        ),
                    },
                    "required_waypoints": {
                        "type": "array",
                        "items": {
                            "type": "string",
                        },
                        "description": (
                            "Places that the route should pass through."
                        ),
                    },
                },
                "required": [
                    "origin",
                    "destination",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "geocode_location",
            "description": (
                "Resolve an ambiguous or unrecognized location name, "
                "place, address, landmark, road, or Singapore locality "
                "into geographic coordinates. Use this when a location "
                "cannot be reliably resolved directly. Do not use this "
                "for routing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": (
                             "The exact location phrase from the user. "
                            "Pass it through unchanged. For example, "
                            "'bukit batok west mall' must be passed as "
                            "'bukit batok west mall'."
                        ),
                    },
                },
                "required": [
                    "location",
                ],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "decide_routing_strategy",
            "description": (
                "Decide whether an operational order should use "
                "simple point-to-point fleet routing or fleet-wide "
                "CVRP optimisation. Use this after an order has "
                "been created and compatibility has been evaluated."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "ID of the operational order."
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "evaluate_compatibility",
            "description": (
                "Evaluate which available vehicles are compatible "
                "with an already-created logistics order. "
                "The order requirements have already been assessed. "
                "This tool decides vehicle compatibility but does "
                "not assign a vehicle or create a route."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": (
                            "The ID of the existing logistics order "
                            "to evaluate."
                        ),
                    },
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "simple_fleet_route",
            "description": (
                "Execute a simple operational route for a single routable order. "
                "Use this after an order has been created, vehicle compatibility "
                "has been evaluated, and the routing strategy is SIMPLE. "
                "The tool selects a compatible vehicle, applies the order's "
                "routing constraints, constructs the vehicle route on the "
                "operational road graph, assigns the vehicle to the order, "
                "persists the route in WorldState, and marks the vehicle as "
                "EN_ROUTE. This is an operational action and modifies WorldState."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": (
                            "The ID of the operational order to route, "
                            "for example ORDER-7C9834E8."
                        ),
                    },
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "geocode_order",
            "description": (
                "Geocode the pickup and delivery locations of an existing operational order "
                "and persist the resulting coordinates and graph nodes into WorldState. "
                "Call this before operational routing when an order has not yet been geocoded."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "ID of the existing order to geocode."
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False
            }
        }
    }
]