import osmnx as ox
from services.world.world_manager import world_manager



def snap_to_graph(state):

    world = world_manager.get_world()

    G = world.graph

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
