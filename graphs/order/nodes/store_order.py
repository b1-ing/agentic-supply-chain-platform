from langsmith import traceable


@traceable(name="Store Order")
def store_order(state):

    state.world.new_orders.append(state.order)

    print(state.world.new_orders)

    print(state.world.orders_in_progress)

    return state
