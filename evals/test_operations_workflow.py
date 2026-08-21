import pytest

from deepeval import assert_test
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval
from services.world.world_manager import world_manager
from app.initialise import initialise_world

# IMPORTANT:
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
            "Determine whether the agent selected the appropriate "
            "operational tools to fulfil the user's request. "
            "The expected output specifies the required tool or tools. "
            "The actual output contains the tools actually called. "
            "The exact order of tool calls does not matter. "
            "Repeated calls are acceptable when they are part of a "
            "valid recovery or operational workflow."
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
# Helper
# ============================================================

def get_tool_names(result):
    return [
        call["name"]
        for call in result["tool_calls"]
    ]


def make_test_case(user_input, actual_tools, expected_tools):

    return LLMTestCase(
        input=user_input,
        actual_output=(
            "Tools called by the agent: "
            + ", ".join(actual_tools)
        ),
        expected_output=(
            "The agent should call: "
            + ", ".join(expected_tools)
        ),
    )


# ============================================================
# 1. Observe complete WorldState
# ============================================================

#
# @pytest.mark.asyncio
# async def test_modify_pending_order():
#
#     agent = OperationsAgent()
#
#     result = await agent.run(
#         "Create an order to deliver 10kg of office supplies "
#         "from Jurong East mrt to Clementi Mall."
#     )
#
#     # 2. Get the newly-created order from WorldState
#     world = world_manager.get_world()
#
#     order = world.new_orders[-1]
#     order_id = order.order_id
#
#     print("Created order:", order_id)
#
#     # 3. Pass the ID into the next agent input
#     user_input = (
#         f"Change order {order_id}'s delivery location to Orchard Road."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "modify_order"
#     ]
#
#     test_case = make_test_case(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#     metric = create_tool_workflow_metric()
#
#     assert_test(
#         test_case,
#         [metric],
#     )
#
#
# @pytest.mark.asyncio
# async def test_observe_world_state():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "Give me a summary of the current operational world, "
#         "including vehicles, orders and active routes."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "get_world_state",
#     ]
#
#     test_case = make_test_case(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#     metric = create_tool_workflow_metric()
#
#     assert_test(
#         test_case,
#         [metric],
#     )
#
#
# # ============================================================
# # 2. Observe available vehicles
# # ============================================================
#
# @pytest.mark.asyncio
# async def test_observe_available_vehicles():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "Which vehicles are currently available?"
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "get_world_state",
#     ]
#
#     test_case = make_test_case(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#     metric = create_tool_workflow_metric()
#
#     assert_test(
#         test_case,
#         [metric],
#     )
#
#
# # ============================================================
# # 3. Observe active routes
# # ============================================================
#
# @pytest.mark.asyncio
# async def test_observe_active_routes():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "Show me the routes currently being executed."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "get_world_state",
#     ]
#
#     test_case = make_test_case(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#     metric = create_tool_workflow_metric()
#
#     assert_test(
#         test_case,
#         [metric],
#     )
#
#
# # ============================================================
# # 4. Observe traffic incidents
# # ============================================================
#
# @pytest.mark.asyncio
# async def test_observe_traffic_incidents():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "What traffic incidents are currently active?"
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "get_traffic_incidents",
#     ]
#
#     test_case = make_test_case(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#     metric = create_tool_workflow_metric()
#
#     assert_test(
#         test_case,
#         [metric],
#     )
#
#
# # ============================================================
# # 5. Observe traffic and affected operations
# # ============================================================
#
# @pytest.mark.asyncio
# async def test_assess_traffic_impact():
#
#     agent = OperationsAgent()
#
#     user_input = (
#         "Check the current traffic situation and tell me "
#         "whether any active operations may be affected."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "get_traffic_incidents",
#         "get_world_state",
#     ]
#
#     test_case = make_test_case(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#     metric = create_tool_workflow_metric()
#
#     assert_test(
#         test_case,
#         [metric],
#     )
#
#
# # ============================================================
# # 6. Modify a pending order
# # ============================================================
# @pytest.mark.asyncio
# async def test_modify_pending_order_no_id():
#
#     agent = OperationsAgent()
#
#     await agent.run(
#         "Create an order to deliver 10kg of office supplies "
#         "from Jurong East MRT to Clementi Mall."
#     )
#
#     user_input = (
#         "Change the delivery location of that order "
#         "to Orchard Road."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     test_case = LLMTestCase(
#         input=user_input,
#         actual_output=(
#             "Tools called by the agent: "
#             + ", ".join(actual_tools)
#         ),
#         expected_output=(
#             "The agent should not modify any order because "
#             "the request does not uniquely identify which "
#             "order to modify."
#         ),
#     )
#
#     metric = create_tool_workflow_metric()
#
#     assert_test(
#         test_case,
#         [metric],
#     )
#
# # ============================================================
# # 7. Modify order weight
# # ============================================================
#
#
#
# @pytest.mark.asyncio
# async def test_modify_pending_order():
#
#     agent = OperationsAgent()
#
#     result = await agent.run(
#         "Create an order to deliver 10kg of office supplies "
#         "from Jurong East mrt to Clementi Mall."
#     )
#
#     # 2. Get the newly-created order from WorldState
#     world = world_manager.get_world()
#
#     order = world.new_orders[-1]
#     order_id = order.order_id
#
#     print("Created order:", order_id)
#
#     # 3. Pass the ID into the next agent input
#     result = await agent.run(
#         f"Change order {order_id} to deliver 10kg of bricks."
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "modify_active_order"
#     ]
#
#     test_case = make_test_case(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#     metric = create_tool_workflow_metric()
#
#     assert_test(
#         test_case,
#         [metric],
#     )
#
#     result = await agent.run(user_input)
#
#     actual_tools = get_tool_names(result)
#
#     expected_tools = [
#         "modify_order",
#     ]
#
#     test_case = make_test_case(
#         user_input,
#         actual_tools,
#         expected_tools,
#     )
#
#     metric = create_tool_workflow_metric()
#
#     assert_test(
#         test_case,
#         [metric],
#     )


# ============================================================
# 8. Delete / cancel a pending order
# ============================================================

@pytest.mark.asyncio
async def test_delete_pending_order():

    agent = OperationsAgent()

    await agent.run(
        "Create an order delivering 5kg of documents "
        "from Bedok MRT to Raffles Place MRT."
    )

    user_input = (
        "Delete all pending orders."
    )

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "delete_order",
        "get_world_state"
    ]

    test_case = make_test_case(
        user_input,
        actual_tools,
        expected_tools,
    )

    metric = create_tool_workflow_metric()

    assert_test(
        test_case,
        [metric],
    )


# ============================================================
# 9. Modify an active order
# ============================================================

@pytest.mark.asyncio
async def test_modify_active_order():

    agent = OperationsAgent()

    await agent.run(
        "Deliver 10kg of refrigerated fish "
        "from Bukit Timah Plaza to Clementi Mall."
    )

    user_input = (
        "Change the delivery location of the active order "
        "to IMM Building."
    )

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "modify_active_order",
    ]

    test_case = make_test_case(
        user_input,
        actual_tools,
        expected_tools,
    )

    metric = create_tool_workflow_metric()

    assert_test(
        test_case,
        [metric],
    )


# ============================================================
# 10. Cancel an active order
# ============================================================

@pytest.mark.asyncio
async def test_cancel_active_order():

    agent = OperationsAgent()

    await agent.run(
        "Deliver 10kg of refrigerated fish "
        "from Bukit Timah Plaza to Clementi Mall."
    )

    user_input = (
        "Cancel the active delivery."
    )

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "cancel_active_order",
    ]

    test_case = make_test_case(
        user_input,
        actual_tools,
        expected_tools,
    )

    metric = create_tool_workflow_metric()

    assert_test(
        test_case,
        [metric],
    )

# ============================================================
# 11. Reroute an active order
# ============================================================

@pytest.mark.asyncio
async def test_dynamic_reroute():

    agent = OperationsAgent()

    await agent.run(
        "Deliver 10kg of refrigerated fish "
        "from Bukit Timah Plaza to Clementi Mall."
    )

    user_input = (
        "PIE is closed, reroute affected"
    )

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "report_traffic_incident",
        "find_affected_routes",
        "reroute_affected_routes"
    ]

    test_case = make_test_case(
        user_input,
        actual_tools,
        expected_tools,
    )

    metric = create_tool_workflow_metric()

    assert_test(
        test_case,
        [metric],
    )


@pytest.mark.asyncio
async def test_modify_goods_with_requirement():

    agent = OperationsAgent()

    await agent.run(
        "Deliver 10kg of bricks "
        "from Bukit Timah Plaza to Clementi Mall."
    )

    user_input = (
        "Change to deliver 20kg of cold fish."
    )

    result = await agent.run(user_input)

    actual_tools = get_tool_names(result)

    expected_tools = [
        "modify_active_order",
        "evaluate_compatibility",
    ]

    test_case = make_test_case(
        user_input,
        actual_tools,
        expected_tools,
    )

    metric = create_tool_workflow_metric()

    assert_test(
        test_case,
        [metric],
    )
