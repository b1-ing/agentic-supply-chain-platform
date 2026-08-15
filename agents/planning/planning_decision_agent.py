import json
import asyncio
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from models.world.planning_decision import PlanningDecision


SYSTEM_PROMPT = """
You are an intelligent logistics planning agent.

You are responsible for deciding WHETHER route optimisation should be run.

You are NOT responsible for computing routes.

Your responsibilities are:

- Determine whether replanning is required.
- Determine whether the entire fleet or only part of it should be replanned.
- Decide which vehicles should be included.
- Decide the optimisation objective.
- Explain your reasoning.

Consider:

- Newly received orders
- Vehicle utilisation
- Existing routes
- Traffic incidents
- Vehicle capacities
- Delivery deadlines
- Current fleet availability

Return ONLY a structured PlanningDecision.

Guidelines:

should_replan
- true if the routing solution should be recomputed.
- false if existing routes remain acceptable.

scope
One of:
- "none"
- "single_vehicle"
- "partial"
- "global"

affected_vehicles
- Empty for fleet replanning.
- List of vehicle IDs for partial replanning.

objective
One of:
- "travel_time"
- "distance"
- "balanced"
- "deadlines"

reason
A concise explanation for the decision.

summary
A one-paragraph summary suitable for displaying on the dashboard.

Return ONLY raw, valid JSON. Do not write any markdown code fences like ```json or trailing text.
"""


class PlanningDecisionAgent:
    def __init__(self, use_local: bool = True):

        if use_local:
            print("[*] Configuring PlanningDecisionAgent to use local model...")

            self.llm_engine = ChatOpenAI(
                model="gemma3:4b",
                base_url="http://localhost:11434/v1",
                api_key="sk-your-key",
                temperature=0.0,
            )

        else:
            print("[*] Configuring PlanningDecisionAgent to use OpenAI...")

            self.llm_engine = ChatOpenAI(
                model="gpt-4.1",
                temperature=0.0,
            )

        self.llm = self.llm_engine.with_structured_output(PlanningDecision)

        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "{world_summary}"),
            ]
        )

    async def run(
        self,
        world,
    ) -> PlanningDecision:

        world_summary = self._summarise_world(world)

        chain = self.prompt | self.llm

        return await chain.ainvoke(
            {
                "world_summary": json.dumps(
                    world_summary,
                    indent=2,
                    default=str,
                )
            }
        )

    def _summarise_world(self, world):

        return {
            # "depots": [
            #     {
            #         "id": depot.depot_id,
            #         "graph_node": depot.graph_node,
            #     }
            #     for depot in world.depots
            # ],
            "vehicles": [
                {
                    "id": vehicle.vehicle_id,
                    "status": vehicle.status,
                    "current_node": vehicle.current_node,
                    "capacity_kg": vehicle.max_weight_kg,
                    "remaining_capacity_kg": getattr(
                        vehicle,
                        "remaining_capacity_kg",
                        None,
                    ),
                    "route_assigned": bool(getattr(vehicle, "route", None)),
                }
                for vehicle in world.vehicles
            ],
            #
            # Orders waiting to be planned
            #
            "new_orders": [
                {
                    "id": order.order_id,
                    "pickup_node": order.pickup_node,
                    "delivery_node": order.delivery_node,
                    "weight_kg": order.weight_kg,
                    "refrigerated": order.refrigerated,
                    "hazardous": order.hazardous,
                    "fragile": order.fragile,
                    "oversized": order.oversized,
                    "latest_delivery": order.latest_delivery,
                }
                for order in world.new_orders
            ],
            #
            # Orders already assigned / executing
            #
            "orders_in_progress": [
                {
                    "id": order.order_id,
                    "pickup_node": order.pickup_node,
                    "delivery_node": order.delivery_node,
                }
                for order in world.orders_in_progress
            ],
            #
            # Orders removed since the previous planning cycle
            #
            "cancelled_orders": [
                {
                    "id": order.order_id,
                }
                for order in world.cancelled_orders
            ],
            #
            # Live traffic events
            #
            "traffic_events": [
                {
                    "type": event.type,
                    "road": event.road_name,
                    "description": event.message,
                    "severity": getattr(event, "severity", None),
                }
                for event in world.traffic_events
            ],
            #
            # Already mapped traffic events
            #
            "matched_events": [
                {
                    "road": getattr(event, "road_name", None),
                    "affected_edges": len(getattr(event, "affected_edges", [])),
                }
                for event in world.matched_events
            ],
            #
            # Current routes
            #
            "routes": [
                {
                    "vehicle": route.vehicle_id,
                    "stops": len(route.stops),
                    "distance": route.total_distance,
                    "travel_time": route.total_travel_time,
                }
                for route in world.routes
            ],
            #
            # Previous planning information
            #
            "previous_replan_recommended": world.recommend_replan,
            "previous_summary": world.summary,
        }
