# agent/tools/order_tools.py

from uuid import uuid4
import os
from services.routing.compatibility_service import CompatibilityService
from openai import AsyncOpenAI
from models.routing.compatibility_result import CompatibilityStatus
from models.order.order_assessment import OrderAssessment
from services.world.world_manager import world_manager
from models.order.incoming_order import IncomingOrder
from models.order.order_constraint import OrderConstraint
import json
from models.vehicles.vehicle import VehicleStatus
from agents.tools.routing_tools import simple_fleet_route



client = AsyncOpenAI(
    api_key=os.environ["OPENAI_API_KEY"]
)

world = world_manager.get_world()

depot_context = [
    {
        "depot_id": depot.depot_id,
        "name": depot.depot_id,
    }
    for depot in world.depots
]

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
- flyovers
- bridges
- viaducts
- ramps
- interchanges
- junctions
- road segments

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


The system may contain known depots.

When the user refers to a depot using phrases such as:

- "the depot"
- "the depot in the system"
- "our depot"
- "the system depot"

you MUST resolve it against the provided system depot list.

Do not treat a known system depot as an arbitrary address.

If exactly one system depot exists and the user says "the depot",
use that depot's depot_id.

Known system depots:

{DEPOTS}


============================================================
OUTPUT
============================================================

Return exactly one IncomingOrder object.

Do not return explanations, markdown, or additional text.
"""
system_prompt = SYSTEM_PROMPT.replace(
    "{DEPOTS}",
    json.dumps(depot_context, indent=2)
)

async def assess_order(
    prompt: str,
) -> dict:
    """
    Processes a request for a new order from a prompt to operations agent,
    extracting info such as pickup and dropoff points, as well as
    making reasonable and strongly-supported inferences for constraints.

    (Arguably, this should be in another separate agent/order_assessment_agent.py file
    but... yeah. Please help me refactor it)

    Returns a dict dumped from a OrderAssessment object!
    """

    response = await client.responses.parse(
        model="gpt-5.4",
        input=[
            {
                "role": "system",
                "content": system_prompt,
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



async def create_order(
    assessment: dict,
) -> dict:
    """
    Creates an IncomingOrder object based on the OrderAssessment-style
    dict created from assess_order.
    """

    missing_information = assessment.get(
        "missing_information",
        []
    )

    #rejects order if there are missing fields
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

#     # 3. Defensive scrubbing BEFORE re-instantiation
#     if "constraints" in data:
#         cleaned_constraints = []
#         for c in data.get("constraints"):
#             # Normalize common LLM typos/truncations dynamically
#             c_type = c.get("type")
#             if c_type == "minimize_delay":
#                 c["type"] = "minimize_unnecessary_delay"
#                 c_type = "minimize_unnecessary_delay"
#
#             # Only keep it if it belongs to your literal Enum list
#             if c_type in VALID_ROUTING_TYPES:
#                 cleaned_constraints.append(c)
    #creates new incomingorder object
    order = IncomingOrder(
        pickup_address=data["pickup_address"],
        delivery_address=data["delivery_address"],

        weight_kg=data.get("weight_kg"),

        refrigerated=data.get("refrigerated", False),
        hazardous=data.get("hazardous", False),
        fragile=data.get("fragile", False),
        oversized=data.get("oversized", False),

        height_m=data.get("height_m"),

        earliest_pickup=data.get("earliest_pickup"),
        latest_pickup=data.get("latest_pickup"),
        earliest_delivery=data.get("earliest_delivery"),
        latest_delivery=data.get("latest_delivery"),

#         constraints=[
#             OrderConstraint(**constraint)
#             for constraint in cleaned_constraints
#         ],
        constraints=data.get("constraints"),

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



async def evaluate_compatibility(
    order_id: str,
) -> dict:
    """
    Calls the evaluate compatibility service, which then calls the compatibility agent.
    """

    service = CompatibilityService()

    return await service.evaluate(
        world,
        order_id,
    )

def _find_order(
    order_id: str,
):
    """
    Find an order in WorldState.

    Returns:
        (order, collection_name)
    """

    world = world_manager.get_world()

    collections = [
        ("new_orders", world.new_orders),
        ("orders_in_progress", world.orders_in_progress),
        ("cancelled_orders", world.cancelled_orders),
        ("unserviceable_orders", world.unserviceable_orders),
    ]

    for collection_name, orders in collections:
        for order in orders:
            if order.order_id == order_id:
                return order, collection_name

    return None, None


async def modify_order(
    order_id: str,
    updates: dict,
) -> dict:
    """
    Modify an existing UNPLANNED order.

    Only explicitly supplied fields are changed.

    Routing-derived fields cannot be modified directly.
    """

    world = world_manager.get_world()

    order, collection_name = _find_order(
        order_id,
    )

    if order is None:
        return {
            "success": False,
            "error": f"Order '{order_id}' not found.",
        }

    if not updates:
        return {
            "success": False,
            "error": "No updates were provided.",
        }

    # ---------------------------------------------------------
    # Fields that must be changed through other tools/workflows
    # ---------------------------------------------------------

    protected_fields = {
        "order_id",
        "assigned_vehicle",
        "pickup_lat",
        "pickup_lon",
        "delivery_lat",
        "delivery_lon",
        "pickup_node",
        "delivery_node",
    }

    protected = protected_fields.intersection(
        updates.keys()
    )

    if protected:
        return {
            "success": False,
            "order_id": order_id,
            "error": (
                "The following fields cannot be modified directly: "
                + ", ".join(sorted(protected))
            ),
        }

    # ---------------------------------------------------------
    # Only allow fields that actually exist on IncomingOrder
    # ---------------------------------------------------------

    valid_fields = set(
        IncomingOrder.model_fields.keys()
    )

    unknown_fields = [
        field
        for field in updates
        if field not in valid_fields
    ]

    if unknown_fields:
        return {
            "success": False,
            "order_id": order_id,
            "error": (
                "Unknown order fields: "
                + ", ".join(unknown_fields)
            ),
        }

    # ---------------------------------------------------------
    # Do not silently modify an order that is already in progress
    # ---------------------------------------------------------

    if collection_name == "orders_in_progress":
        return {
            "success": False,
            "order_id": order_id,
            "error": (
                "Order is currently in progress. "
                "Modifying an in-progress order requires "
                "the operational replanning workflow."
            ),
        }

    # ---------------------------------------------------------
    # Save old values
    # ---------------------------------------------------------

    previous_values = {
        field: getattr(order, field)
        for field in updates
    }

    # ---------------------------------------------------------
    # Apply updates
    # ---------------------------------------------------------

    try:
        for field, value in updates.items():
            setattr(order, field, value)

    except Exception as exc:
        for field, value in previous_values.items():
            setattr(order, field, value)
        return {
            "success": False,
            "order_id": order_id,
            "error": f"Failed to modify order: {exc}",
        }

    # ---------------------------------------------------------
    # Address changes invalidate existing geocoding
    # ---------------------------------------------------------

    routing_invalidated = False

    if "pickup_address" in updates:

        order.pickup_lat = None
        order.pickup_lon = None
        order.pickup_node = None

        routing_invalidated = True

    if "delivery_address" in updates:

        order.delivery_lat = None
        order.delivery_lon = None
        order.delivery_node = None

        routing_invalidated = True

    return {
        "success": True,
        "order_id": order_id,
        "updated_fields": list(updates.keys()),
        "previous_values": previous_values,
        "routing_invalidated": routing_invalidated,
        "message": (
            f"Order '{order_id}' modified successfully."
        ),
    }


async def delete_order(
    order_id: str,
) -> dict:
    """
    Delete a UNPLANNED order from WorldState.

    NEW orders can be deleted directly.

    Orders currently in progress cannot be deleted directly.

    In-progress orders must use the cancel_active_order tool.
    """

    world = world_manager.get_world()

    # ---------------------------------------------------------
    # NEW
    # ---------------------------------------------------------

    for index, order in enumerate(world.new_orders):

        if order.order_id == order_id:

            world.new_orders.pop(index)

            return {
                "success": True,
                "order_id": order_id,
                "previous_collection": "new_orders",
                "message": (
                    f"Order '{order_id}' deleted successfully."
                ),
            }

    # ---------------------------------------------------------
    # IN PROGRESS
    # ---------------------------------------------------------

    for order in world.orders_in_progress:

        if order.order_id == order_id:

            return {
                "success": False,
                "order_id": order_id,
                "error": (
                    "Order is currently in progress and cannot "
                    "be deleted directly. Cancel or replan the "
                    "associated route first."
                ),
            }

    # ---------------------------------------------------------
    # CANCELLED
    # ---------------------------------------------------------

    for index, order in enumerate(world.cancelled_orders):

        if order.order_id == order_id:

            world.cancelled_orders.pop(index)

            return {
                "success": True,
                "order_id": order_id,
                "previous_collection": "cancelled_orders",
                "message": (
                    f"Order '{order_id}' deleted successfully."
                ),
            }

    # ---------------------------------------------------------
    # UNSERVICEABLE
    # ---------------------------------------------------------

    for index, order in enumerate(
        world.unserviceable_orders
    ):

        if order.order_id == order_id:

            world.unserviceable_orders.pop(index)

            return {
                "success": True,
                "order_id": order_id,
                "previous_collection": "unserviceable_orders",
                "message": (
                    f"Order '{order_id}' deleted successfully."
                ),
            }

    return {
        "success": False,
        "order_id": order_id,
        "error": f"Order '{order_id}' not found.",
    }

# ============================================================
# MODIFY ACTIVE ORDER
# ============================================================
async def modify_active_order(
    order_id: str,
    updates: dict,
) -> dict:
    """
    Modify an order that is currently in progress.

    If the modification affects routing, the active route is
    immediately rebuilt from the vehicle's current position
    through the order's updated remaining stops.

    Important:
        - The order itself is updated first.
        - Pickup/delivery RouteStops are updated to reflect the
          new order locations.
        - Routing constraints are extracted from the updated order.
        - The existing VehicleRoute object is then rerouted.
    """

    world = world_manager.get_world()

    # ============================================================
    # FIND ACTIVE ORDER
    # ============================================================

    order = next(
        (
            order
            for order in world.orders_in_progress
            if order.order_id == order_id
        ),
        None,
    )

    if order is None:
        return {
            "success": False,
            "order_id": order_id,
            "error": f"Active order '{order_id}' not found.",
        }

    if not updates:
        return {
            "success": False,
            "order_id": order_id,
            "error": "No updates were provided.",
        }

    # ============================================================
    # PROTECTED FIELDS
    # ============================================================

    protected_fields = {
        "order_id",
        "assigned_vehicle",
        "pickup_lat",
        "pickup_lon",
        "delivery_lat",
        "delivery_lon",
        "pickup_node",
        "delivery_node",
    }

    protected = protected_fields.intersection(
        updates.keys()
    )

    if protected:
        return {
            "success": False,
            "order_id": order_id,
            "error": (
                "The following fields cannot be modified directly: "
                + ", ".join(sorted(protected))
            ),
        }

    # ============================================================
    # VALIDATE FIELDS
    # ============================================================

    valid_fields = set(
        IncomingOrder.model_fields.keys()
    )

    unknown_fields = [
        field
        for field in updates
        if field not in valid_fields
    ]

    if unknown_fields:
        return {
            "success": False,
            "order_id": order_id,
            "error": (
                "Unknown order fields: "
                + ", ".join(unknown_fields)
            ),
        }

    # ============================================================
    # SAVE PREVIOUS VALUES
    # ============================================================

    previous_values = {
        field: getattr(order, field)
        for field in updates
    }

    # ============================================================
    # DETERMINE WHETHER ROUTING IS INVALIDATED
    # ============================================================

    routing_fields = {
        "pickup_address",
        "delivery_address",
        "weight_kg",
        "height_m",
        "width_m",
        "length_m",
        "refrigerated",
        "hazardous",
        "fragile",
        "oversized",
        "earliest_pickup",
        "latest_pickup",
        "earliest_delivery",
        "latest_delivery",
        "constraints",
    }

    routing_invalidated = bool(
        routing_fields.intersection(
            updates.keys()
        )
    )

    # ============================================================
    # APPLY ORDER UPDATES
    # ============================================================

    try:
        for field, value in updates.items():
            setattr(
                order,
                field,
                value,
            )

    except Exception as exc:
        for field, value in previous_values.items():
            setattr(
                order,
                field,
                value,
            )
        return {
            "success": False,
            "order_id": order_id,
            "error": (
                f"Failed to modify active order: {exc}"
            ),
        }

    if routing_invalidated:

        # --------------------------------------------------------
        # Re-evaluate compatibility after the order modification.
        #
        # The existing vehicle may no longer be capable of
        # servicing the modified order.
        # --------------------------------------------------------

        compatibility_service = CompatibilityService()

        compatibility = await compatibility_service.evaluate(
            world,
            order_id,
        )

        print(compatibility)

        if compatibility.status == CompatibilityStatus.UNSERVICEABLE:
            for field, value in previous_values.items():
                setattr(
                    order,
                    field,
                    value,
                )
            return {
                "success": False,
                "order_id": order_id,
                "error": (
                    "The modified order is no longer serviceable "
                    "by any available vehicle."
                ),
            }

        if compatibility.status == CompatibilityStatus.WAITING:
            for field, value in previous_values.items():
                setattr(
                    order,
                    field,
                    value,
                )
            return {
                "success": False,
                "order_id": order_id,
                "status": "WAITING",
                "error": (
                    "The modified order currently has no compatible "
                    "vehicle available."
                ),
            }

        # --------------------------------------------------------
        # Determine whether the currently assigned vehicle is
        # still allowed to service the modified order.
        # --------------------------------------------------------

        allowed_vehicle_indices = (
            compatibility.allowed_vehicle_indices
        )

        current_vehicle = next(
            (
                vehicle
                for vehicle in world.vehicles
                if vehicle.vehicle_id == order.assigned_vehicle
            ),
            None,
        )

        current_vehicle_index = None

        if current_vehicle is not None:
            current_vehicle_index = world.vehicles.index(
                current_vehicle
            )

        current_vehicle_still_compatible = (
            current_vehicle_index is not None
            and current_vehicle_index in allowed_vehicle_indices
        )

        # --------------------------------------------------------
        # Existing vehicle is still valid.
        # --------------------------------------------------------

        if current_vehicle_still_compatible:

            vehicle = current_vehicle

        # --------------------------------------------------------
        # Existing vehicle is no longer valid.
        #
        # Example:
        #
        #   Before modification:
        #       Vehicle A = normal truck
        #
        #   After modification:
        #       order.refrigerated = True
        #
        #   Vehicle A is now incompatible.
        #
        #   Select another compatible vehicle.
        # --------------------------------------------------------

        else:

            compatible_vehicle_index = (
                allowed_vehicle_indices[0]
                if allowed_vehicle_indices
                else None
            )

            if compatible_vehicle_index is None:
                for field, value in previous_values.items():
                    setattr(
                        order,
                        field,
                        value,
                    )
                return {
                    "success": False,
                    "order_id": order_id,
                    "status": "UNSERVICEABLE",
                    "error": (
                        "The currently assigned vehicle is no longer "
                        "compatible with the modified order, and no "
                        "replacement vehicle is available."
                    ),
                }

            vehicle = world.vehicles[
                compatible_vehicle_index
            ]

            # Remove the old assignment.
            order.assigned_vehicle = vehicle.vehicle_id

        # --------------------------------------------------------
        # Determine whether the order remains on its existing
        # vehicle or needs to be reassigned.
        # --------------------------------------------------------

        vehicle_changed = (
            current_vehicle is not None
            and vehicle.vehicle_id != current_vehicle.vehicle_id
        )

        route = None

        # ========================================================
        # CASE 1: SAME VEHICLE
        #
        # The existing vehicle is still compatible, so we can
        # modify/reroute its existing operational route.
        # ========================================================

        if not vehicle_changed:

            current_route_id = getattr(
                vehicle,
                "current_route_id",
                None,
            )

            if current_route_id is not None:

                route = next(
                    (
                        existing_route
                        for existing_route in world.routes
                        if existing_route.route_id == current_route_id
                    ),
                    None,
                )

            # Fallback
            if route is None:

                route = getattr(
                    vehicle,
                    "current_route",
                    None,
                )

            if route is None:
                for field, value in previous_values.items():
                    setattr(
                        order,
                        field,
                        value,
                    )

                return {
                    "success": False,
                    "order_id": order_id,
                    "error": (
                        f"Vehicle '{vehicle.vehicle_id}' "
                        "does not have an active route."
                    ),
                }


        # ========================================================
        # CASE 2: REPLACEMENT VEHICLE
        #
        # The old vehicle is no longer compatible.
        #
        # The replacement vehicle does NOT need an existing route.
        # A new route will be constructed later.
        # ========================================================

        else:

            # Preserve the old vehicle so its route can be cleaned up.
            old_vehicle = current_vehicle

            old_route = None

            old_route_id = getattr(
                old_vehicle,
                "current_route_id",
                None,
            )

            if old_route_id is not None:

                old_route = next(
                    (
                        existing_route
                        for existing_route in world.routes
                        if existing_route.route_id == old_route_id
                    ),
                    None,
                )

            if old_route is None:

                old_route = getattr(
                    old_vehicle,
                    "current_route",
                    None,
                )

            # ----------------------------------------------------
            # Remove the old vehicle's active route.
            # ----------------------------------------------------

            if old_route is not None:

                if old_route in world.routes:
                    world.routes.remove(old_route)

                old_vehicle.current_route_id = None
                old_vehicle.current_route = None

                # Only return the old vehicle to AVAILABLE if it
                # has no other operational work.
                old_vehicle.status = VehicleStatus.IDLE

            # ----------------------------------------------------
            # Replacement vehicle starts with no active route.
            # ----------------------------------------------------

            route = None

    # ============================================================
    # RESOLVE NEW ADDRESSES
    # ============================================================

    if (
        "pickup_address" in updates
        or "delivery_address" in updates
    ):

        from agents.tools.geocoding_tools import (
            geocode_location,
        )

        import osmnx as ox

        # --------------------------------------------------------
        # NEW PICKUP
        # --------------------------------------------------------

        if "pickup_address" in updates:

            result = geocode_location(
                order.pickup_address
            )

            if not result["success"]:
                for field, value in previous_values.items():
                    setattr(
                        order,
                        field,
                        value,
                    )
                return {
                    "success": False,
                    "order_id": order_id,
                    "error": (
                        "Failed to geocode new pickup "
                        f"location: "
                        f"{result.get('error')}"
                    ),
                }

            order.pickup_lat = result["latitude"]
            order.pickup_lon = result["longitude"]

            order.pickup_node = (
                ox.distance.nearest_nodes(
                    world.graph,
                    order.pickup_lon,
                    order.pickup_lat,
                )
            )

        # --------------------------------------------------------
        # NEW DELIVERY
        # --------------------------------------------------------

        if "delivery_address" in updates:

            result = geocode_location(
                order.delivery_address
            )

            if not result["success"]:
                for field, value in previous_values.items():
                    setattr(
                        order,
                        field,
                        value,
                    )
                return {
                    "success": False,
                    "order_id": order_id,
                    "error": (
                        "Failed to geocode new delivery "
                        f"location: "
                        f"{result.get('error')}"
                    ),
                }

            order.delivery_lat = result["latitude"]
            order.delivery_lon = result["longitude"]

            order.delivery_node = (
                ox.distance.nearest_nodes(
                    world.graph,
                    order.delivery_lon,
                    order.delivery_lat,
                )
            )

    # ============================================================
    # UPDATE ROUTE STOPS
    #
    # THIS IS THE IMPORTANT PART.
    #
    # The old RouteStop still points at the old pickup/delivery
    # RoutingLocation. Replace it with the location from the
    # updated order.
    # ============================================================

    if routing_invalidated and route is not None:

        from models.order.routing_location import (
            RoutingLocation,
        )

        for stop in route.stops:

            location = getattr(
                stop,
                "location",
                None,
            )

            if location is None:
                continue

            stop_order_id = getattr(
                location,
                "order_id",
                None,
            )

            stop_kind = getattr(
                location,
                "kind",
                None,
            )

            # Only modify stops belonging to this order
            if stop_order_id != order.order_id:
                continue

            # ----------------------------------------------------
            # UPDATE PICKUP STOP
            # ----------------------------------------------------

            if (
                stop_kind == "pickup"
                and (
                    "pickup_address" in updates
                    or "constraints" in updates
                )
            ):

                stop.location = RoutingLocation(
                    matrix_index=0,
                    graph_node=order.pickup_node,
                    lat=order.pickup_lat,
                    lon=order.pickup_lon,
                    kind="pickup",
                    order_id=order.order_id,
                )

            # ----------------------------------------------------
            # UPDATE DELIVERY STOP
            # ----------------------------------------------------

            elif (
                stop_kind == "delivery"
                and (
                    "delivery_address" in updates
                    or "constraints" in updates
                )
            ):

                stop.location = RoutingLocation(
                    matrix_index=0,
                    graph_node=order.delivery_node,
                    lat=order.delivery_lat,
                    lon=order.delivery_lon,
                    kind="delivery",
                    order_id=order.order_id,
                )

    # ============================================================
    # EXTRACT UPDATED ROUTING CONSTRAINTS
    # ============================================================

    avoid_roads = []
    avoid_areas = []
    required_waypoints = []

    for constraint in order.constraints or []:

        # --------------------------------------------------------
        # Support both:
        #
        #   OrderConstraint(...)
        #
        # and:
        #
        #   {"type": "...", "value": "..."}
        # --------------------------------------------------------

        if isinstance(constraint, dict):

            constraint_type = constraint.get(
                "type"
            )

            value = constraint.get(
                "value"
            )

        else:

            constraint_type = getattr(
                constraint,
                "type",
                None,
            )

            value = getattr(
                constraint,
                "value",
                None,
            )

        # --------------------------------------------------------
        # Convert Enum -> string
        # --------------------------------------------------------

        if hasattr(
            constraint_type,
            "value",
        ):
            constraint_type = (
                constraint_type.value
            )

        # --------------------------------------------------------
        # Extract routing constraints
        # --------------------------------------------------------

        if constraint_type == "avoid_road":

            avoid_roads.append(
                str(value)
            )

        elif constraint_type == "avoid_area":

            avoid_areas.append(
                str(value)
            )

        elif constraint_type == "required_waypoint":

            required_waypoints.append(
                str(value)
            )

    # ============================================================
    # REROUTE
    # ============================================================

    reroute_result = None

    if routing_invalidated:

        world.recommend_replan = True

        from services.traffic.disruption_service import (
            DisruptionService,
        )

        disruption_service = DisruptionService()

        # ========================================================
        # Existing vehicle
        #
        # Reroute its existing operational route.
        # ========================================================

        if route is not None:

            reroute_result = (
                await disruption_service.reroute_route(
                    world=world,
                    route=route,
                    vehicle=vehicle,
                    avoid_roads=avoid_roads,
                    avoid_areas=avoid_areas,
                )
            )

        # ========================================================
        # Replacement vehicle
        #
        # There is no existing route to reroute.
        # Build a fresh route from the replacement vehicle's
        # current position -> pickup -> delivery.
        # ========================================================

        else:

            from agents.tools.routing_tools import (
                simple_routing_tool,
            )
            from models.order.routing_location import (
                RoutingLocation,
            )
            from models.routing.route_segment import (
                RouteSegment,
            )
            from models.routing.route_stop import (
                RouteStop,
            )
            from models.routing.vehicle_route import (
                VehicleRoute,
            )
            from uuid import uuid4

            # ----------------------------------------------------
            # Build routing locations
            # ----------------------------------------------------

            origin = RoutingLocation(
                matrix_index=0,
                graph_node=vehicle.current_node,
                lat=vehicle.current_lat,
                lon=vehicle.current_lon,
                kind="vehicle",
            )

            pickup = RoutingLocation(
                matrix_index=1,
                graph_node=order.pickup_node,
                lat=order.pickup_lat,
                lon=order.pickup_lon,
                kind="pickup",
                order_id=order.order_id,
            )

            delivery = RoutingLocation(
                matrix_index=2,
                graph_node=order.delivery_node,
                lat=order.delivery_lat,
                lon=order.delivery_lon,
                kind="delivery",
                order_id=order.order_id,
            )

            # ----------------------------------------------------
            # Build route legs
            # ----------------------------------------------------

            legs = [
                (origin, pickup),
                (pickup, delivery),
                (delivery, origin),
            ]

            segments = []

            total_distance = 0.0
            total_travel_time = 0.0

            for leg_origin, leg_destination in legs:

                result = simple_routing_tool.route_locations(
                    world=world,
                    origin=leg_origin,
                    destination=leg_destination,
                    avoid_roads=avoid_roads,
                    avoid_areas=avoid_areas,
                    required_waypoints=required_waypoints,
                )

                if not result["success"]:
                    for field, value in previous_values.items():
                        setattr(
                            order,
                            field,
                            value,
                        )
                    return {
                        "success": False,
                        "order_id": order_id,
                        "vehicle_id": vehicle.vehicle_id,
                        "status": "UNROUTABLE",
                        "error": result.get("error"),
                    }

                route_data = result["route"]

                segment = RouteSegment(
                    nodes=route_data["nodes"],
                    geometry=route_data["geometry"],
                    distance=route_data["distance_m"],
                    travel_time=route_data["travel_time_s"],
                    instructions=[],
                )

                segments.append(segment)

                total_distance += route_data["distance_m"]
                total_travel_time += route_data["travel_time_s"]

            # ----------------------------------------------------
            # Build new route
            # ----------------------------------------------------

            route_id = (
                f"ROUTE-{uuid4().hex[:8].upper()}"
            )

            route = VehicleRoute(
                route_id=route_id,
                vehicle_id=vehicle.vehicle_id,
                stops=[
                    RouteStop(
                        sequence=0,
                        location=origin,
                    ),
                    RouteStop(
                        sequence=1,
                        location=pickup,
                    ),
                    RouteStop(
                        sequence=2,
                        location=delivery,
                    ),
                    RouteStop(
                        sequence=3,
                        location=origin,
                    ),
                ],
                segments=segments,
                total_distance=total_distance,
                total_travel_time=total_travel_time,
            )

            # ----------------------------------------------------
            # Commit new route
            # ----------------------------------------------------

            vehicle.current_route_id = route_id
            vehicle.current_route = route
            vehicle.status = VehicleStatus.EN_ROUTE

            world.routes.append(route)

            reroute_result = {
                "success": True,
                "routing_mode": "graph",
                "route_id": route_id,
                "vehicle_id": vehicle.vehicle_id,
                "distance_m": total_distance,
                "travel_time_s": total_travel_time,
                "message": (
                    "Order reassigned to a compatible vehicle "
                    "and a new route was constructed."
                ),
            }

    # ============================================================
    # RETURN
    # ============================================================

    return {
        "success": True,
        "order_id": order_id,
        "updated_fields": list(
            updates.keys()
        ),
        "previous_values": previous_values,
        "routing_invalidated": routing_invalidated,
        "recommend_replan": routing_invalidated,
        "status": "IN_PROGRESS",
        "message": (
            f"Active order '{order_id}' "
            "modified successfully."
        ),
        "reroute": reroute_result,
    }

# ============================================================
# CANCEL ACTIVE ORDER
# ============================================================

async def cancel_active_order(
    order_id: str,
    reason: str = "",
) -> dict:
    """
    Cancel an order currently in progress.

    The order is removed from active execution and moved to
    world.cancelled_orders.

    The associated vehicle route is marked for replanning.
    """

    world = world_manager.get_world()

    # ---------------------------------------------------------
    # Find active order
    # ---------------------------------------------------------

    order = next(
        (
            order
            for order in world.orders_in_progress
            if order.order_id == order_id
        ),
        None,
    )

    if order is None:
        return {
            "success": False,
            "order_id": order_id,
            "error": (
                f"Active order '{order_id}' not found."
            ),
        }

    # ---------------------------------------------------------
    # Find associated vehicle
    # ---------------------------------------------------------

    vehicle = None

    if order.assigned_vehicle:
        vehicle = next(
            (
                v
                for v in world.vehicles
                if v.vehicle_id == order.assigned_vehicle
            ),
            None,
        )

    # ---------------------------------------------------------
    # Find associated route
    # ---------------------------------------------------------

    route = None

    if order.assigned_vehicle:
        route = next(
            (
                r
                for r in world.routes
                if r.vehicle_id == order.assigned_vehicle
            ),
            None,
        )

    # ---------------------------------------------------------
    # Cancel order
    # ---------------------------------------------------------

    world.orders_in_progress.remove(order)

    if order not in world.cancelled_orders:
        world.cancelled_orders.append(order)

    # ---------------------------------------------------------
    # Clear order assignment
    # ---------------------------------------------------------

    order.assigned_vehicle = None

    # ---------------------------------------------------------
    # Vehicle becomes available for replanning
    # ---------------------------------------------------------

    if vehicle is not None:
        vehicle.current_route_id = None
        vehicle.current_route = None
        vehicle.status = VehicleStatus.IDLE

    # ---------------------------------------------------------
    # Remove obsolete route
    # ---------------------------------------------------------

    if route is not None:
        world.routes.remove(route)

    # ---------------------------------------------------------
    # Replanning may be required for the fleet
    # ---------------------------------------------------------

    world.recommend_replan = True



    return {
        "success": True,
        "order_id": order_id,
        "status": "CANCELLED",
        "reason": reason,
        "vehicle_id": (
            vehicle.vehicle_id
            if vehicle
            else None
        ),
        "route_id": (
            route.route_id
            if route
            else None
        ),
        "recommend_replan": True,
        "message": (
            f"Active order '{order_id}' cancelled successfully."
        ),
    }
