import osmnx as ox


def snap_to_graph(state):

    G = state.world.graph

    order = state.order

    order.pickup_node = ox.distance.nearest_nodes(
        G,
        order.pickup_lon,
        order.pickup_lat,
    )

    order.delivery_node = ox.distance.nearest_nodes(
        G,
        order.delivery_lon,
        order.delivery_lat,
    )

    return state
