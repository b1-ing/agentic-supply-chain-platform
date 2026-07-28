import networkx as nx

from models.order.incoming_order import IncomingOrder
from models.vehicles.standard_truck import StandardTruck
from services.routing.routing_service import RoutingService
from services.routing.route_visualiser import RouteVisualiser
from services.world.world_manager import world_manager


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def build_test_graph() -> nx.MultiDiGraph:

    graph = nx.MultiDiGraph()

    coordinates = {
        0: (103.800, 1.300),
        1: (103.801, 1.301),
        2: (103.802, 1.302),
        3: (103.803, 1.303),
        4: (103.804, 1.304),
    }

    for node, (lon, lat) in coordinates.items():
        graph.add_node(
            node,
            x=lon,
            y=lat,
        )

    edges = [
        (0, 1),
        (1, 0),
        (1, 2),
        (2, 1),
        (2, 3),
        (3, 2),
        (3, 4),
        (4, 3),
        (4, 0),
        (0, 4),
    ]

    for u, v in edges:
        graph.add_edge(
            u,
            v,
            travel_time=5,
            length=500,
        )

    return graph


def initialise_world(num_vehicles: int = 1):

    graph = build_test_graph()

    vehicles = []

    for i in range(num_vehicles):

        vehicles.append(
            StandardTruck(
                vehicle_id=f"truck-{i}",
                current_node=0,
            )
        )

    world_manager.initialise(
        graph=graph,
        vehicles=vehicles,
    )

    world = world_manager.get_world()

    world.new_orders.extend(
        [
            IncomingOrder(
                order_id="order-1",
                pickup_address="A",
                delivery_address="B",
                pickup_node=1,
                delivery_node=2,
                pickup_lat=1.301,
                pickup_lon=103.801,
                delivery_lat=1.302,
                delivery_lon=103.802,
                weight_kg=20,
            ),
            IncomingOrder(
                order_id="order-2",
                pickup_address="C",
                delivery_address="D",
                pickup_node=3,
                delivery_node=4,
                pickup_lat=1.303,
                pickup_lon=103.803,
                delivery_lat=1.304,
                delivery_lon=103.804,
                weight_kg=30,
            ),
        ]
    )

    return world


# ---------------------------------------------------------
# Tests
# ---------------------------------------------------------

def test_full_routing_pipeline():

    world = initialise_world()

    routing_service = RoutingService()

    route_plan = routing_service.plan_routes(world)

    assert route_plan is not None
    assert len(route_plan.routes) == 1

    route = route_plan.routes[0]

    assert len(route.stops) > 0
    assert len(route.segments) > 0

    assert route.total_distance > 0
    assert route.total_travel_time > 0

    RouteVisualiser().save(
        route_plan,
        "output/test_full_pipeline.html",
    )


def test_multiple_vehicles():

    world = initialise_world(num_vehicles=2)

    routing_service = RoutingService()

    route_plan = routing_service.plan_routes(world)

    assert len(route_plan.routes) == 2

    RouteVisualiser().save(
        route_plan,
        "output/test_multiple_vehicles.html",
    )


def test_pickups_before_deliveries():

    world = initialise_world()

    routing_service = RoutingService()

    route_plan = routing_service.plan_routes(world)

    route = route_plan.routes[0]

    for order in world.new_orders:

        pickup_index = next(
            i
            for i, stop in enumerate(route.stops)
            if stop.location.kind == "pickup"
            and stop.location.order_id == order.order_id
        )

        delivery_index = next(
            i
            for i, stop in enumerate(route.stops)
            if stop.location.kind == "delivery"
            and stop.location.order_id == order.order_id
        )

        assert pickup_index < delivery_index