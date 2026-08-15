TRAFFIC_TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "report_traffic_incident",
            "description": (
                "Report a new traffic incident such as a road closure, "
                "accident, roadworks, or other disruption."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "road_name": {
                        "type": ["string", "null"],
                        "description": "Name of the affected road or road segment."
                    },
                    "incident_type": {
                        "type": "string",
                        "description": "Type of traffic incident."
                    },
                    "description": {
                        "type": "string",
                        "description": "Description of the incident."
                    },
                    "severity": {
                        "type": "number",
                        "description": "Incident severity from 0 to 1."
                    },
                    "latitude": {
                        "type": ["number", "null"],
                        "description": "Latitude of the incident, if known."
                    },
                    "longitude": {
                        "type": ["number", "null"],
                        "description": "Longitude of the incident, if known."
                    },
                    "end_time": {
                        "type": ["string", "null"],
                        "description": "Optional ISO-8601 end time."
                    }
                },
                "required": [
                    "road_name",
                    "incident_type",
                    "description",
                    "severity",
                    "latitude",
                    "longitude",
                    "end_time"
                ],
                "additionalProperties": False
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "get_traffic_incidents",
            "description": (
                "Get all currently active traffic incidents in the WorldState."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "find_affected_routes",
            "description": (
                "Find currently active vehicle routes affected by "
                "a specific traffic incident."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "ID of the traffic incident."
                    }
                },
                "required": [
                    "incident_id"
                ],
                "additionalProperties": False
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "reroute_affected_routes",
            "description": (
                "Reroute all currently active vehicle routes affected "
                "by a specific traffic incident."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "incident_id": {
                        "type": "string",
                        "description": "ID of the traffic incident."
                    }
                },
                "required": [
                    "incident_id"
                ],
                "additionalProperties": False
            }
        }
    }
]

ORDER_TOOL_SCHEMAS=[
    {
    "type": "function",
    "function": {
        "name": "modify_active_order",
        "description": (
            "Modify an order that is currently in progress. "
            "Changes to routing-relevant fields invalidate the "
            "current route and mark the world as requiring replanning."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "ID of the active order to modify."
                },
                "updates": {
                    "type": "object",
                    "description": (
                        "Fields to update on the active order. "
                        "Do not include protected routing-derived fields."
                    ),
                    "additionalProperties": True
                }
            },
            "required": [
                "order_id",
                "updates"
            ],
            "additionalProperties": False
        }
    }
    },
    {
        "type": "function",
        "function": {
            "name": "cancel_active_order",
            "description": (
                "Cancel an order that is currently in progress. "
                "Moves the order to cancelled_orders, releases its "
                "assigned vehicle, removes its current route, and "
                "marks the world as requiring replanning."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "ID of the active order to cancel."
                    },
                    "reason": {
                        "type": "string",
                        "description": "Optional reason for cancellation."
                    }
                },
                "required": [
                    "order_id"
                ],
                "additionalProperties": False
            }
        }
    }
]

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
    },
    {
        "type": "function",
        "function": {
            "name": "modify_order",
            "description": (
                "Modify an existing order that has not yet entered active "
                "execution. Use this when the user wants to change order "
                "details such as weight, addresses, cargo requirements, "
                "time windows, notes, or routing constraints. "
                "Do not modify routing-derived fields such as coordinates, "
                "graph nodes, or vehicle assignment directly."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": (
                            "The ID of the order to modify, for example "
                            "'ORDER-12345678'."
                        ),
                    },
                    "updates": {
                        "type": "object",
                        "description": (
                            "Fields to change on the order. Only include "
                            "fields that the user explicitly wants changed."
                        ),
                        "properties": {
                            "pickup_address": {
                                "type": ["string", "null"],
                            },
                            "delivery_address": {
                                "type": ["string", "null"],
                            },
                            "weight_kg": {
                                "type": ["number", "null"],
                            },
                            "height_m": {
                                "type": ["number", "null"],
                            },
                            "refrigerated": {
                                "type": ["boolean", "null"],
                            },
                            "hazardous": {
                                "type": ["boolean", "null"],
                            },
                            "fragile": {
                                "type": ["boolean", "null"],
                            },
                            "oversized": {
                                "type": ["boolean", "null"],
                            },
                            "earliest_pickup": {
                                "type": ["string", "null"],
                            },
                            "latest_pickup": {
                                "type": ["string", "null"],
                            },
                            "earliest_delivery": {
                                "type": ["string", "null"],
                            },
                            "latest_delivery": {
                                "type": ["string", "null"],
                            },
                            "constraints": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": [
                                                "avoid_road",
                                                "avoid_area",
                                                "required_road",
                                                "required_area",
                                                "required_waypoint",
                                                "max_route_time",
                                                "max_route_distance",
                                                "minimize_unnecessary_delay",
                                            ],
                                        },
                                        "value": {},
                                        "hard": {
                                            "type": "boolean",
                                        },
                                        "reason": {
                                            "type": ["string", "null"],
                                        },
                                    },
                                    "required": [
                                        "type",
                                        "value",
                                        "hard",
                                        "reason",
                                    ],
                                    "additionalProperties": False,
                                },
                            },
                            "notes": {
                                "type": ["string", "null"],
                            },
                        },
                        "additionalProperties": False,
                    },
                },
                "required": [
                    "order_id",
                    "updates",
                ],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_order",
            "description": (
                "Delete an order from the operational world state. "
                "Use this when the user explicitly asks to remove or "
                "delete an order. Orders currently in progress cannot "
                "be deleted directly and require cancellation or "
                "replanning instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": (
                            "The ID of the order to delete."
                        ),
                    },
                },
                "required": [
                    "order_id",
                ],
                "additionalProperties": False,
            },
        },
    },
    *TRAFFIC_TOOL_SCHEMAS,
    *ORDER_TOOL_SCHEMAS
]
