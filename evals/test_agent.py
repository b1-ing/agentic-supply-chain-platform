from deepeval import assert_test
from deepeval.test_case import LLMTestCase, LLMTestCaseParams
from deepeval.metrics import GEval


def test_agent_response():
    test_case = LLMTestCase(
        input="Deliver 10kg of refrigerated fish from Bukit Timah Plaza to Clementi Mall.",
        actual_output="Order created and routed using a refrigerated vehicle.",
        expected_output=(
            "The order should be assessed as refrigerated, "
            "assigned a compatible vehicle, and routed."
        ),
    )

    metric = GEval(
        name="Task Correctness",
        criteria=(
            "Determine whether the actual output correctly reflects "
            "the expected operational outcome."
        ),
        evaluation_params=[
            LLMTestCaseParams.ACTUAL_OUTPUT,
            LLMTestCaseParams.EXPECTED_OUTPUT,
        ],
        threshold=0.5,
    )

    assert_test(test_case, [metric])