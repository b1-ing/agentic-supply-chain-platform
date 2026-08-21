import pytest

from deepeval import assert_test
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCase, LLMTestCaseParams

from app.initialise import initialise_world

# WorldState must be initialised before importing OperationsAgent.
initialise_world()

from agents.operations_agent import OperationsAgent


# ============================================================
# DeepEval metric
# ============================================================

def create_tool_workflow_metric():
    return GEval(
        name="Tool Workflow Correctness",
        criteria=(
            "Evaluate whether the agent selected an appropriate set of "
            "operational tools to fulfil the user's request. "
            "The actual output contains the tools called by the agent. "
            "The expected output describes the tools that should be "
            "involved in a successful workflow. "
            "Do not require an exact tool ordering. "
            "Additional tool calls are acceptable if they are reasonable "
            "prerequisites, retries, observations, or recovery actions. "
            "The workflow should contain the required operational "
            "capabilities needed to complete the request."
        ),
        evaluation_params=[
            LLMTestCaseParams.INPUT,
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        model="gpt-5.4-mini-2026-03-17",
        threshold=0.5,
    )


# ============================================================
# Helpers
# ============================================================

def get_tool_names(result):
    return [
        call["name"]
        for call in result["tool_calls"]
    ]


def evaluate_tool_workflow(
    user_input,
    actual_tools,
    expected_tools,
):
    """
    Run a DeepEval evaluation of the agent's tool workflow.
    """

    test_case = LLMTestCase(
        input=user_input,

        actual_output=(
            "The agent called the following tools:\n"
            + ", ".join(actual_tools)
        ),

        expected_output=(
            "A successful workflow should use the following "
            "operational capabilities:\n"
            + ", ".join(expected_tools)
        ),
    )

    metric = create_tool_workflow_metric()

    assert_test(
        test_case,
        [metric],
    )

    print("\nExpected:", expected_tools)
    print("Actual:  ", actual_tools)


# ============================================================
# 1. Basic refrigerated delivery
# ============================================================
#
# @pytest.mark.asyncio
# async def test_refrigerated_delivery_tool_workflow():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "Deliver 10kg of refrigerated fish "
#         "from Bukit Timah Plaza to Clementi Mall."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "assess_order",
#         "create_order",
#         "evaluate_compatibility",
#         "decide_routing_strategy",
#         "geocode_order",
#         "simple_fleet_route",
#     ]
#
#     evaluate_tool_workflow(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#
# # ============================================================
# # 2. Normal non-refrigerated delivery
# # ============================================================
#
# @pytest.mark.asyncio
# async def test_normal_delivery_tool_workflow():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "Deliver 5kg of office supplies "
#         "from Jurong East to Raffles Place."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "assess_order",
#         "create_order",
#         "evaluate_compatibility",
#         "decide_routing_strategy",
#         "geocode_order",
#         "simple_fleet_route",
#     ]
#
#     evaluate_tool_workflow(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#
# # ============================================================
# # 3. Depot resolution
# # ============================================================
#
# @pytest.mark.asyncio
# async def test_depot_resolution_tool_workflow():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "Deliver 5kg of office supplies "
#         "from the depot to Raffles Place."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "assess_order",
#         "create_order",
#         "evaluate_compatibility",
#         "decide_routing_strategy",
#         "geocode_order",
#         "simple_fleet_route",
#     ]
#
#     evaluate_tool_workflow(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#
# # ============================================================
# # 4. Avoid road constraint
# # ============================================================
#
# @pytest.mark.asyncio
# async def test_avoid_road_delivery_tool_workflow():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "Deliver 8kg of electronics "
#         "from Tampines Mall to Orchard Road. "
#         "Avoid PIE."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "assess_order",
#         "create_order",
#         "evaluate_compatibility",
#         "decide_routing_strategy",
#         "geocode_order",
#         "simple_fleet_route",
#     ]
#
#     evaluate_tool_workflow(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#
# # ============================================================
# # 5. Heavy delivery
# # ============================================================
#
# @pytest.mark.asyncio
# async def test_heavy_delivery_tool_workflow():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "Deliver 500kg of construction materials "
#         "from Tuas to Woodlands."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "assess_order",
#         "create_order",
#         "evaluate_compatibility",
#         "decide_routing_strategy",
#         "geocode_order",
#         "simple_fleet_route",
#     ]
#
#     evaluate_tool_workflow(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#
# # ============================================================
# # 6. Fragile delivery
# # ============================================================
#
# @pytest.mark.asyncio
# async def test_fragile_delivery_tool_workflow():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "Deliver 15kg of fragile laboratory equipment "
#         "from One-North to Changi Business Park."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "assess_order",
#         "create_order",
#         "evaluate_compatibility",
#         "decide_routing_strategy",
#         "geocode_order",
#         "simple_fleet_route",
#     ]
#
#     evaluate_tool_workflow(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )


# ============================================================
# 7. Hazardous delivery
# ============================================================

@pytest.mark.asyncio
async def test_hazardous_delivery_tool_workflow():

    agent = OperationsAgent()

    user_input = (
        "Deliver 20kg of hazardous chemicals "
        "from Jurong Island to Tuas South."
    )

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "assess_order",
    ]

    evaluate_tool_workflow(
        user_input,
        actual_tools,
        expected_tools,
    )


# ============================================================
# 8. Oversized delivery
# ============================================================

@pytest.mark.asyncio
async def test_oversized_delivery_tool_workflow():

    agent = OperationsAgent()

    user_input = (
        "Deliver an oversized 100kg machine "
        "from Changi to Tuas. "
        "The shipment is 3 metres wide."
    )

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "assess_order",
        "create_order",
        "evaluate_compatibility",
        "decide_routing_strategy",
        "geocode_order",
        "simple_fleet_route",
    ]

    evaluate_tool_workflow(
        user_input,
        actual_tools,
        expected_tools,
    )


# ============================================================
# 9. Delivery with time constraint
# ============================================================

@pytest.mark.asyncio
async def test_time_constrained_delivery_tool_workflow():

    agent = OperationsAgent()

    user_input = (
        "Deliver 30kg of food supplies "
        "from Bedok to Marina Bay. "
        "The delivery must arrive before 5pm."
    )

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "assess_order",
        "create_order",
        "evaluate_compatibility",
        "decide_routing_strategy",
        "geocode_order",
        "simple_fleet_route",
    ]

    evaluate_tool_workflow(
        user_input,
        actual_tools,
        expected_tools,
    )


# ============================================================
# 10. Multiple orders → fleet optimisation
# ============================================================

@pytest.mark.asyncio
async def test_multi_order_fleet_planning_workflow():

    agent = OperationsAgent()

    user_input = """
    Create and plan the following deliveries together:

    1. Deliver 20kg from Jurong East to Clementi.
    2. Deliver 30kg from Bukit Timah to Queenstown.
    3. Deliver 15kg from Toa Payoh to Paya Lebar.
    4. Deliver 25kg from Tampines to Changi.

    Plan the fleet routes efficiently.
    """

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "assess_order",
        "create_order",
        "evaluate_compatibility",
        "decide_routing_strategy",
        "plan_routes",
    ]

    evaluate_tool_workflow(
        user_input,
        actual_tools,
        expected_tools,
    )


# ============================================================
# 11. Natural-language location routing
# ============================================================

@pytest.mark.asyncio
async def test_natural_language_location_tool_workflow():

    agent = OperationsAgent()

    user_input = (
        "Route a vehicle from DSTA to Changi Airport."
    )

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "route",
    ]

    evaluate_tool_workflow(
        user_input,
        actual_tools,
        expected_tools,
    )


# ============================================================
# 12. Multiple refrigerated orders → fleet optimisation
# ============================================================

@pytest.mark.asyncio
async def test_multiple_refrigerated_orders_tool_workflow():

    agent = OperationsAgent()

    user_input = """
    I need these refrigerated deliveries planned:

    1. 20kg of fresh seafood from Jurong East to Clementi.
    2. 15kg of frozen meat from Bukit Timah to Orchard.
    3. 25kg of dairy products from Tampines to Changi.

    Optimise the vehicle assignments and routes.
    """

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "assess_order",
        "create_order",
        "evaluate_compatibility",
        "decide_routing_strategy",
        "plan_routes",
    ]

    evaluate_tool_workflow(
        user_input,
        actual_tools,
        expected_tools,
    )