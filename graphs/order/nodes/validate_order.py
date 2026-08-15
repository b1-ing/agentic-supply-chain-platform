from langsmith import traceable


@traceable(name="Validate Order")
def validate_order(state):

    order = state.order

    errors = []

    if not order.pickup_address:
        errors.append("Pickup address is required.")

    if not order.delivery_address:
        errors.append("Delivery address is required.")

    if order.weight_kg and order.weight_kg < 0:
        errors.append("Weight cannot be negative.")


    if (
        order.earliest_delivery
        and order.latest_delivery
        and order.earliest_delivery > order.latest_delivery
    ):
        errors.append("Delivery time window is invalid.")

    state.validation_errors = errors
    state.valid = len(errors) == 0

    return state
