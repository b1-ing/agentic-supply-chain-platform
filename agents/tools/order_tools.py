# agent/tools/order_tools.py

from uuid import uuid4
import os
from services.routing.compatibility_service import CompatibilityService
from openai import AsyncOpenAI

from models.order.order_assessment import OrderAssessment
from services.world.world_manager import world_manager
from models.order.incoming_order import IncomingOrder
from models.order.order_constraint import OrderConstraint



async def create_order(
    assessment: dict,
) -> dict:

    missing_information = assessment.get(
        "missing_information",
        []
    )

    if missing_information:
        return {
            "success": False,
            "error": "Order assessment is missing required information.",
            "missing_information": missing_information,
        }

    data = assessment

    world = world_manager.get_world()

    VALID_ROUTING_TYPES = {
                "avoid_road", "avoid_area", "required_road", "required_area",
                "required_waypoint", "max_route_time", "max_route_distance",
                "minimize_unnecessary_delay"
            }

    # 3. Defensive scrubbing BEFORE re-instantiation
    if "constraints" in data:
        cleaned_constraints = []
        for c in data.get("constraints"):
            # Normalize common LLM typos/truncations dynamically
            c_type = c.get("type")
            if c_type == "minimize_delay":
                c["type"] = "minimize_unnecessary_delay"
                c_type = "minimize_unnecessary_delay"

            # Only keep it if it belongs to your literal Enum list
            if c_type in VALID_ROUTING_TYPES:
                cleaned_constraints.append(c)

    order = IncomingOrder(
        pickup_address=data["pickup_address"],
        delivery_address=data["delivery_address"],

        weight_kg=data.get("weight_kg"),
        volume_m3=data.get("volume_m3"),
        pallets=data.get("pallets"),

        refrigerated=data.get("refrigerated", False),
        hazardous=data.get("hazardous", False),
        fragile=data.get("fragile", False),
        oversized=data.get("oversized", False),

        height_m=data.get("height_m"),

        earliest_pickup=data.get("earliest_pickup"),
        latest_pickup=data.get("latest_pickup"),
        earliest_delivery=data.get("earliest_delivery"),
        latest_delivery=data.get("latest_delivery"),

        constraints=[
            OrderConstraint(**constraint)
            for constraint in cleaned_constraints
        ],

        notes=data.get("notes"),
    )

    order.order_id = (
        order.order_id
        or f"ORDER-{uuid4().hex[:8].upper()}"
    )

    world.new_orders.append(order)

    return {
        "success": True,
        "order_id": order.order_id,
        "status": "NEW",
    }
client = AsyncOpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)
SYSTEM_PROMPT = """
You are the order-assessment component of an agentic supply-chain
management system.

Convert the user's natural-language logistics request into exactly
one structured IncomingOrder object.

Your job is to:
1. Extract information explicitly stated by the user.
2. Make only reasonable, strongly-supported logistics inferences.
3. Put information into the correct IncomingOrder fields.
4. Extract explicit routing constraints.

You do NOT:
- assign vehicles
- check vehicle compatibility
- create routes
- calculate routes, distance, or travel time
- modify WorldState


============================================================
GENERAL RULES
============================================================

- Return exactly one object matching the provided schema.
- Never invent information.
- Preserve user-provided names and values.
- Unknown values must be null.
- Do not geocode locations.
- Do not replace a user's explicitly stated location or road with
  another location or road.


============================================================
ORDER INFORMATION
============================================================

Extract these fields when explicitly stated:

LOCATIONS:
- pickup_address
- delivery_address

CARGO:
- weight_kg
- volume_m3
- pallets
- height_m
- width_m
- length_m

VEHICLE REQUIREMENTS:
- refrigerated
- hazardous
- fragile
- oversized

TIME WINDOWS:
- earliest_pickup
- latest_pickup
- earliest_delivery
- latest_delivery

Convert units where necessary:
- tonnes → kilograms
- dimensions → metres
- route distance → metres
- route time → seconds


============================================================
CARGO REQUIREMENTS
============================================================

These are IncomingOrder fields, NOT routing constraints.

Cold, frozen, chilled, or temperature-sensitive cargo:
→ refrigerated = true

Fuel, LPG, flammable, corrosive, toxic, or dangerous goods:
→ hazardous = true

Glass, artwork, delicate equipment, or clearly fragile cargo:
→ fragile = true

Abnormal, oversized, very large, unusually wide/tall equipment:
→ oversized = true

If an explicit dimension is provided, extract the dimension AND set
oversized = true when it clearly implies oversized transport.

NEVER create routing constraints such as:
- require_refrigeration
- require_hazardous_vehicle
- require_fragile_vehicle
- require_oversized_vehicle
- require_cold_chain
- require_vehicle


============================================================
ROUTING CONSTRAINTS
============================================================

The constraints field is ONLY for instructions about how the vehicle
should travel.

The ONLY allowed constraint types are:

- avoid_road
- avoid_area
- required_road
- required_area
- required_waypoint
- max_route_time
- max_route_distance
- minimize_unnecessary_delay

NEVER invent another constraint type.

If a requested constraint does not fit one of the types above,
do not create a new type.


------------------------------------------------------------
AVOID / REQUIRED ROAD
------------------------------------------------------------

Use a ROAD type when the value is a named:

- road
- street
- avenue
- drive
- expressway
- highway
- parkway
- road segment
- transport corridor

Examples:

"avoid Clementi Road"
→ avoid_road, value="Clementi Road"

"avoid PIE"
→ avoid_road, value="PIE"

"avoid Pan Island Expressway"
→ avoid_road, value="Pan Island Expressway"

"go via Holland Road"
→ required_road, value="Holland Road"


Singapore expressway abbreviations are roads:

PIE, AYE, KJE, BKE, CTE, ECP, KPE, MCE, SLE, TPE


------------------------------------------------------------
AVOID / REQUIRED AREA
------------------------------------------------------------

Use an AREA type only when the value is a geographic:

- region
- district
- neighbourhood
- estate
- zone
- area

Examples:

"avoid Jurong East"
→ avoid_area, value="Jurong East"

"avoid the CBD"
→ avoid_area, value="CBD"

"route through the CBD"
→ required_area, value="CBD"


------------------------------------------------------------
WAYPOINT
------------------------------------------------------------

Use required_waypoint when the user explicitly requires a stop or
waypoint.

Example:

"stop at Jurong Port"
→ required_waypoint, value="Jurong Port"


------------------------------------------------------------
ROUTE LIMITS
------------------------------------------------------------

"complete within 30 minutes"
→ max_route_time, value=1800

"keep the route under 20km"
→ max_route_distance, value=20000


------------------------------------------------------------
ROUTING PREFERENCES
------------------------------------------------------------

minimize_unnecessary_delay may be inferred when strongly justified.

Examples:
- perishable cargo
- time-sensitive cargo
- fragile cargo

It should normally be:
hard = false

Do not invent other routing preferences such as:
- avoid highways
- avoid tolls
- avoid bridges
- avoid CBD
- avoid residential areas

unless explicitly requested.


============================================================
HARD / SOFT
============================================================

Explicit mandatory instructions:
→ hard = true

Examples:
- must avoid PIE
- do not use Clementi Road
- must go via Holland Road
- must arrive by 4pm

Inferred preferences:
→ hard = false


============================================================
IMPORTANT CLASSIFICATION RULE
============================================================

For every routing constraint:

1. Identify what the user explicitly named.
2. Preserve its value exactly.
3. Determine whether that value is a ROAD or AREA.
4. Select ONLY the corresponding allowed constraint type.

A named road MUST NOT become an area.

Examples:

"avoid Clementi Road"
→ {
    "type": "avoid_road",
    "value": "Clementi Road"
}

"avoid PIE"
→ {
    "type": "avoid_road",
    "value": "PIE"
}

"avoid the CBD"
→ {
    "type": "avoid_area",
    "value": "CBD"
}

NEVER output:
{
    "type": "avoid_area",
    "value": "Clementi Road"
}

NEVER output:
{
    "type": "avoid_highway",
    "value": "PIE"
}

NEVER output any constraint type other than the eight allowed types.


============================================================
OUTPUT
============================================================

Return exactly one IncomingOrder object.

Do not return explanations, markdown, or additional text.
"""


async def assess_order(
    prompt: str,
) -> dict:

    response = await client.responses.parse(
        model="gpt-5.4",
        input=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        text_format=OrderAssessment,
    )

    assessment = response.output_parsed

    if assessment is None:
        raise RuntimeError(
            "GPT-5.4 did not return a structured order assessment."
        )

    return assessment.model_dump()

async def evaluate_compatibility(
    order_id: str,
) -> dict:

    service = CompatibilityService()

    return await service.evaluate(
        order_id,
    )