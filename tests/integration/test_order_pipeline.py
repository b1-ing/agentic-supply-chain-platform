from pprint import pprint
import osmnx as ox
from models.order.order_state import OrderState
from models.world.world_state import WorldState
from services.world.world_manager import world_manager
from graphs.order.nodes.assess_order import assess_order
from graphs.order.nodes.validate_order import validate_order
from graphs.order.nodes.geocode import geocode_order
from graphs.order.nodes.snap_to_graph import snap_to_graph
from graphs.order.nodes.store_order import store_order


def print_stage(title: str, state: OrderState):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    print("\nOrder")
    pprint(state.order)

    print("\nValid")
    pprint(getattr(state, "valid", None))

    print("\nValidation Errors")
    pprint(getattr(state, "validation_errors", None))

    if getattr(state.order, "pickup_coord", None):
        print("\nPickup")
        pprint(state.order.pickup_coord)

    if getattr(state.order, "delivery_coord", None):
        print("\nDelivery")
        pprint(state.order.delivery_coord)

    if getattr(state.order, "pickup_node", None):
        print("\nPickup Node")
        pprint(state.order.pickup_node)

    if getattr(state.order, "delivery_node", None):
        print("\nDelivery Node")
        pprint(state.order.delivery_node)


def run_single_test(prompt: str):

    print("\n")
    print("#" * 80)
    print("INPUT")
    print("#" * 80)
    print(prompt)

    graph = ox.load_graphml("cache/singapore.graphml")
    mapping = {}

    world_manager.initialise(
        graph=graph,
        mapping=mapping,  # remove if you've removed depots completely
        vehicles=[],
    )

    state = OrderState(
        raw_order=prompt,
        world=world,
    )

    print_stage("Initial", state)

    pipeline = [
        ("assess_order()", assess_order),
        ("validate_order()", validate_order),
        ("geocode_order()", geocode_order),
        ("snap_to_graph()", snap_to_graph),
        ("store_order()", store_order),
    ]

    for name, node in pipeline:
        if name != "validate_order()" and not getattr(state, "valid", True):
            break

        state = node(state)
        print_stage(f"After {name}", state)

    return state


if __name__ == "__main__":
    prompts = [
        "Deliver 8 pallets of frozen seafood from Jurong Port to Changi Airport before 3 PM.",
        "Transport 500kg of hazardous chemicals from Tuas Port to PSA Pasir Panjang.",
        "Move a fragile MRI scanner from NUH to Singapore General Hospital.",
        "Deliver 20 pallets of electronics from Changi Airfreight Centre to Woodlands.",
        "Pickup furniture at IKEA Alexandra and deliver to Marina Bay Sands tomorrow morning.",
        "Deliver 50 tonnes of steel beams from Depot Road to Sentosa.",
        "Move frozen vaccines from Woodlands to Khoo Teck Puat Hospital before 8am.",
    ]

    world = WorldState()

    for prompt in prompts:
        state = OrderState(
            raw_order=prompt,
            world=world,
        )

        state = run_single_test(prompt)

        print("\nCurrent World Orders")
        pprint(state.world.orders_in_progress)

        print("\nTotal Orders:", len(state.world.new_orders))
