from graphs.order.graph import build_order_graph
from models.order.order_state import OrderState


class OrderWorkflow:
    def __init__(self):

        self.graph = build_order_graph()

    def run(
        self,
        raw_order: str,
    ):

        state = OrderState(
            raw_order=raw_order,
        )

        return self.graph.invoke(state)
