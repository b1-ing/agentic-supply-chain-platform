from services.routing.onemap_routing_service import OneMapRoutingService


def test_route():

    service = OneMapRoutingService()

    result = service.route(
        start_lat=1.3000,
        start_lon=103.8000,
        end_lat=1.3521,
        end_lon=103.8198,
    )

    print(result)

    assert result.travel_time > 0
    assert result.distance > 0
    assert len(result.geometry) > 0