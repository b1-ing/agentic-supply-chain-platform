import osmnx as ox


def snap_to_graph(state):

    G = state.world.graph

    order = state.order

    order.pickup_node = ox.distance.nearest_nodes(
        G,
        order.pickup_coord[1],
        order.pickup_coord[0],
    )

    order.delivery_node = ox.distance.nearest_nodes(
        G,
        order.delivery_coord[1],
        order.delivery_coord[0],
    )

    return state