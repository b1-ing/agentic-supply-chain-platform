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

Compatibility means that the vehicle has the physical and operational
capabilities required to service the order.

IMPORTANT:

Vehicle compatibility and vehicle availability are separate concepts.

A vehicle may be EN_ROUTE and still be compatible with an order.

If a vehicle is already assigned to the order being evaluated, it MUST
still be evaluated for compatibility even if:

- its status is EN_ROUTE
- it has a current_route_id
- it is not otherwise available for a new assignment

An EN_ROUTE vehicle must NOT be excluded from the compatibility result
merely because it is currently operating.

For a vehicle already assigned to the order, determine whether it can
CONTINUE servicing that order under the current order requirements.

A vehicle that is EN_ROUTE because it is servicing a DIFFERENT order
should not be treated as an available replacement vehicle.
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

For each vehicle:

1. Determine whether the vehicle satisfies the order's requirements.
2. If the vehicle is already assigned to this order, evaluate it even
   if it is EN_ROUTE.
3. Do not treat EN_ROUTE status alone as incompatibility.
4. Do not treat AVAILABLE status alone as compatibility.
5. If an important required capability is unknown, mark the vehicle
   as UNCERTAIN rather than assuming compatibility.

A vehicle is COMPATIBLE when there is sufficient evidence that it can
service the order.

A vehicle is INCOMPATIBLE only when there is sufficient evidence that
it cannot satisfy the order requirements.

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

        #finds the target order to evaluate compatibility
        order = None

        for candidate in world.new_orders:
            if candidate.order_id == order_id:
                order = candidate
                break

        #falls back to checking orders in progress if it cannot find target order in
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

        # Build order context

        order_context = {
            "order_id": order.order_id,
            "pickup_address": order.pickup_address,
            "delivery_address": order.delivery_address,

            "weight_kg": order.weight_kg,

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
                    "is_current_order_vehicle": (
                        vehicle.vehicle_id == order.assigned_vehicle
                    ),

                    "max_weight_kg": vehicle.max_weight_kg,

                    "refrigerated": vehicle.refrigerated,
                    "hazardous_certified": vehicle.hazardous_certified,
                    "fragile_capable": vehicle.fragile_capable,

                    "height_m": vehicle.height_m,
                    "width_m": vehicle.width_m,
                    "length_m": vehicle.length_m,
                }
            )

        print(vehicle_context)

        # ---------------------------------------------------------
        # Ask GPT-5.4
        # ---------------------------------------------------------

        payload = {
            "order": order_context,
            "vehicles": vehicle_context,
        }

        response = await self.client.chat.completions.create(
            model="gpt-5.4-nano-2026-03-17",
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