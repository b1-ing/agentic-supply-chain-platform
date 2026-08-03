import osmnx as ox

from services.world.world_manager import world_manager
from services.routing.routing_service import RoutingService
from services.routing.route_visualiser import RouteVisualiser

from graphs.order.nodes.assess_order import assess_order
from graphs.order.nodes.validate_order import validate_order
from graphs.order.nodes.geocode import geocode_order
from graphs.order.nodes.snap_to_graph import snap_to_graph
from graphs.order.nodes.store_order import store_order

from models.order.order_state import OrderState
from models.vehicles.standard_truck import StandardTruck


################################################################################
# Setup
################################################################################

def initialise_world():

    graph = ox.load_graphml("cache/singapore.graphml")

    lat = 1.300557
    lon = 103.799389

    start_node = ox.distance.nearest_nodes(
        graph,
        lon,
        lat,
    )

    vehicles = [
        StandardTruck(
            vehicle_id="truck-1",
            current_node=start_node,
        ),
        StandardTruck(
            vehicle_id="truck-2",
            current_node=start_node,
        ),
    ]

    #
    # Initialise singleton
    #
    world_manager.initialise(
        graph=graph,
        mapping={},
        vehicles=vehicles,
    )

    return world_manager.get_world()


################################################################################
# Order pipeline
################################################################################

def process_order(prompt: str):

    state = OrderState(
        raw_order=prompt,
        world=world_manager.get_world(),
    )

    pipeline = [
        assess_order,
        validate_order,
        geocode_order,
        snap_to_graph,
        store_order,
    ]

    for node in pipeline:

        state = node(state)

        #
        # Validation may fail
        #
        if hasattr(state, "valid"):
            assert state.valid, state.validation_errors

    return state.order


################################################################################
# Full integration test
################################################################################

def test_full_pipeline():

    world = initialise_world()

    prompts = [
        "Deliver 8 pallets of frozen seafood from Jurong Port to Changi Airport before 3 PM.",
        # "Transport 500kg of hazardous chemicals from Tuas Port to PSA Pasir Panjang.",
        # "Move a fragile MRI scanner from NUH to Singapore General Hospital.",
        "Deliver 20 pallets of electronics from Changi Airfreight Centre to Woodlands.",
#       "Pickup furniture at IKEA Alexandra and deliver to Marina Bay Sands tomorrow morning.",
    ]

    ####################################################################
    # Process incoming orders
    ####################################################################

    for prompt in prompts:

        order = process_order(prompt)

        assert order.pickup_node is not None
        assert order.delivery_node is not None

        assert order.pickup_lat is not None
        assert order.pickup_lon is not None

        assert order.delivery_lat is not None
        assert order.delivery_lon is not None

    ####################################################################
    # World should now contain orders
    ####################################################################

    world = world_manager.get_world()

    assert len(world.new_orders) == len(prompts)

    ####################################################################
    # Route planning
    ####################################################################

    routing_service = RoutingService()

    route_plan = routing_service.plan_routes(world)

    assert route_plan is not None
    assert len(route_plan.routes) > 0

    ####################################################################
    # Validate routes
    ####################################################################

    for route in route_plan.routes:

        assert len(route.stops) > 0
        assert len(route.segments) > 0

        assert route.total_distance > 0
        assert route.total_travel_time > 0

        #
        # Every stop should have coordinates
        #
        for stop in route.stops:

            assert stop.location.lat is not None
            assert stop.location.lon is not None

        #
        # Every segment should contain geometry from OneMap
        #
        for segment in route.segments:

            assert segment.geometry
            assert len(segment.geometry) > 1

            assert segment.distance > 0
            assert segment.travel_time > 0

    ####################################################################
    # Visualise
    ####################################################################

    RouteVisualiser().save(
        route_plan,
        output_file="output/full_pipeline.html",
    )

    print("\n==============================================")
    print("Pipeline completed successfully.")
    print("Map written to output/full_pipeline.html")
    print("==============================================")