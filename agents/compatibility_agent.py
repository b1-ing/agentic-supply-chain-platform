from __future__ import annotations

import json

from openai import AsyncOpenAI

from services.world.world_manager import world_manager


SYSTEM_PROMPT = """
You are the vehicle compatibility agent for an agentic
supply-chain management system.

Your job is to determine which available vehicles are compatible
with an ALREADY-ASSESSED logistics order.

The order assessment has already determined what the order requires.
Do NOT reinterpret the original user request and do NOT invent
additional order requirements.

============================================================
RESPONSIBILITY
============================================================

You are responsible for deciding:

- which vehicles are compatible
- which vehicles are incompatible
- why each vehicle is compatible or incompatible
- whether compatibility cannot be determined

You may consider all relevant information provided about:

ORDER:
- weight
- volume
- pallets
- refrigerated requirement
- hazardous requirement
- fragile requirement
- oversized requirement
- height requirements
- width requirements
- length requirements
- explicit operational constraints
- pickup/delivery requirements

VEHICLE:
- status
- current location
- current route
- remaining capacity
- maximum weight
- maximum volume
- pallet capacity
- refrigeration capability
- hazardous certification
- dimensions
- other explicitly provided capabilities

============================================================
IMPORTANT
============================================================

The order assessment is authoritative.

If assess_order says:

    refrigerated = true

then a non-refrigerated vehicle is incompatible.

If assess_order says:

    weight_kg = 500

then the vehicle must have sufficient remaining weight
capacity.

Do NOT change these requirements.

============================================================
DO NOT
============================================================

You MUST NOT:

- create routes
- assign a vehicle to the order
- modify WorldState
- perform CVRP optimisation
- call OR-Tools
- change the order requirements
- invent vehicle capabilities
- infer new cargo requirements

You are making a compatibility decision only.

============================================================
DECISION RULE
============================================================

A vehicle should be marked COMPATIBLE only when the available
information provides sufficient evidence that it can service
the order.

If an important capability is unknown, mark the vehicle as
UNCERTAIN rather than assuming compatibility.

============================================================
OUTPUT
============================================================

Return only the structured compatibility assessment.
"""


class CompatibilityAgent:

    def __init__(self):
        self.client = AsyncOpenAI()

    async def evaluate(self, order_id: str) -> dict:

        world = world_manager.get_world()

        # ---------------------------------------------------------
        # Find order
        # ---------------------------------------------------------

        order = None

        for candidate in world.new_orders:
            if candidate.order_id == order_id:
                order = candidate
                break

        if order is None:
            for candidate in world.orders_in_progress:
                if candidate.order_id == order_id:
                    order = candidate
                    break

        if order is None:
            return {
                "success": False,
                "error": f"Order '{order_id}' not found.",
            }

        # ---------------------------------------------------------
        # Build order context
        #
        # These are already-assessed requirements.
        # Do NOT derive new requirements here.
        # ---------------------------------------------------------

        order_context = {
            "order_id": order.order_id,
            "pickup_address": order.pickup_address,
            "delivery_address": order.delivery_address,

            "weight_kg": order.weight_kg,
            "volume_m3": order.volume_m3,
            "pallets": order.pallets,

            "refrigerated": order.refrigerated,
            "hazardous": order.hazardous,
            "fragile": order.fragile,
            "oversized": order.oversized,

            "height_m": order.height_m,

            "earliest_pickup": order.earliest_pickup,
            "latest_pickup": order.latest_pickup,
            "earliest_delivery": order.earliest_delivery,
            "latest_delivery": order.latest_delivery,

            "notes": order.notes,
        }

        # ---------------------------------------------------------
        # Build fleet context
        # ---------------------------------------------------------

        vehicle_context = []

        for vehicle in world.vehicles:

            vehicle_context.append(
                {
                    "vehicle_id": vehicle.vehicle_id,

                    "status": str(vehicle.status),
                    "current_node": vehicle.current_node,
                    "current_route_id": vehicle.current_route_id,

                    "max_weight_kg": vehicle.max_weight_kg,
                    "max_volume_m3": vehicle.max_volume_m3,
                    "max_pallets": vehicle.max_pallets,

                    "refrigerated": vehicle.refrigerated,
                    "hazardous_certified": vehicle.hazardous_certified,
                    "fragile_capable": vehicle.fragile_capable,

                    "height_m": vehicle.height_m,
                    "width_m": vehicle.width_m,
                    "length_m": vehicle.length_m,
                }
            )

        # ---------------------------------------------------------
        # Ask GPT-5.4
        # ---------------------------------------------------------

        payload = {
            "order": order_context,
            "vehicles": vehicle_context,
        }

        response = await self.client.chat.completions.create(
            model="gpt-5.4",
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        payload,
                        default=str,
                    ),
                },
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "vehicle_compatibility",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "status": {
                                "type": "string",
                                "enum": [
                                    "ROUTABLE",
                                    "UNSERVICEABLE",
                                    "UNCERTAIN",
                                ],
                            },
                            "compatible": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "vehicle_id": {
                                            "type": "string"
                                        },
                                        "reason": {
                                            "type": "string"
                                        },
                                    },
                                    "required": [
                                        "vehicle_id",
                                        "reason",
                                    ],
                                    "additionalProperties": False,
                                },
                            },
                            "incompatible": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "vehicle_id": {
                                            "type": "string"
                                        },
                                        "reason": {
                                            "type": "string"
                                        },
                                    },
                                    "required": [
                                        "vehicle_id",
                                        "reason",
                                    ],
                                    "additionalProperties": False,
                                },
                            },
                            "uncertain": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "vehicle_id": {
                                            "type": "string"
                                        },
                                        "reason": {
                                            "type": "string"
                                        },
                                    },
                                    "required": [
                                        "vehicle_id",
                                        "reason",
                                    ],
                                    "additionalProperties": False,
                                },
                            },
                            "recommended_vehicle_id": {
                                "type": [
                                    "string",
                                    "null",
                                ]
                            },
                            "reasoning": {
                                "type": "string"
                            },
                        },
                        "required": [
                            "status",
                            "compatible",
                            "incompatible",
                            "uncertain",
                            "recommended_vehicle_id",
                            "reasoning",
                        ],
                        "additionalProperties": False,
                    },
                },
            },
        )

        result = json.loads(
            response.choices[0].message.content
        )

        return {
            "success": True,
            "order_id": order_id,
            **result,
        }