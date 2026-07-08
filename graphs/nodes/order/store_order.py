def store_order(state):

    state.world.orders.append(state.order)

    print(state.world.orders)

    return state
