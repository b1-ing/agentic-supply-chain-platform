from agents.order.order_extraction_agent import OrderExtractionAgent
from models.order_state import OrderState


agent = OrderExtractionAgent()


def assess_order(state: OrderState):

    state.order = agent.extract(state.raw_order)

    return state
