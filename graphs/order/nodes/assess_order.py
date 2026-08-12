from uuid import uuid4
from langsmith import traceable
from models.order.order_state import OrderState
from agents.order.order_extraction_agent import OrderExtractionAgent


@traceable
def assess_order(state: OrderState) -> OrderState:
    """
    Extract an IncomingOrder from the raw prompt.

    This is the first node in the pipeline, so generate the
    order ID here.
    """

    order = state.order

    agent = OrderExtractionAgent()

    # First time this order is created
    if order is None:
        order = agent.extract(
            state.raw_order,
        )

        order.order_id = f"ORDER-{uuid4().hex[:8].upper()}"

        state.order = order

    return state
