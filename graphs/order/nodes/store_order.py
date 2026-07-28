def store_order(state):

    state.world.new_orders.append(state.order)

    print(state.world.new_orders)

    return state
