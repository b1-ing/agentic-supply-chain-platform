def store_order(state):

    state.world.orders.append(state.order)

    return state