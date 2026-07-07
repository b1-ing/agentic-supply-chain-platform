from copy import deepcopy
from pprint import pprint

from models.order_state import OrderState
from models.world_state import WorldState

from graphs.nodes.order.assess_order import assess_order
from graphs.nodes.order.validate_order import validate_order
from graphs.nodes.order.geocode import geocode_order
from graphs.nodes.order.snap_to_graph import snap_to_graph
from graphs.nodes.order.store_order import store_order


def print_stage(title: str, state: OrderState):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    print("\nOrder:")
    pprint(state.order)

    print("\nValidation Errors:")
    pprint(getattr(state, "validation_errors", None))

    print("\nValid:")
    pprint(getattr(state, "valid", None))


def run_single_test(prompt: str):

    print("\n")
    print("#" * 80)
    print("INPUT")
    print("#" * 80)
    print(prompt)

    world = WorldState()

    state = OrderState(
        raw_order=prompt,
        world=world,
    )

    print_stage("Initial State", state)

    state = assess_order(state)
    print_stage("After assess_order()", state)

    state = validate_order(state)
    print_stage("After validate_order()", state)

    if getattr(state, "valid", True):

        state = geocode_order(state)
        print_stage("After geocode_order()", state)

        state = snap_to_graph(state)
        print_stage("After snap_to_graph()", state)

        state = store_order(state)
        print_stage("After store_order()", state)

    else:
        print("\nOrder failed validation. Remaining stages skipped.")


if __name__ == "__main__":

    test_prompts = [

        "Deliver 8 pallets of frozen seafood from Jurong Port to Changi Airport before 3 PM.",

        "Transport 500kg of hazardous chemicals from Tuas Port to PSA Pasir Panjang.",

        "Move a fragile MRI scanner from NUH to Singapore General Hospital.",

        "Deliver 20 pallets of electronics from Changi Airfreight Centre to Woodlands.",

        "Pickup furniture at IKEA Alexandra and deliver to Marina Bay Sands tomorrow morning.",

        "Deliver 50 tonnes of steel beams to Sentosa.",

        "Move frozen vaccines from Woodlands to Khoo Teck Puat Hospital before 8am."
    ]

    for prompt in test_prompts:
        run_single_test(prompt)