def serialize_depot(depot) -> dict:
    """
    Serialize a Depot model into a JSON-safe dictionary
    for API responses.
    """

    return {
        "depot_id": depot.depot_id,
        "graph_node": depot.graph_node,
        "lat": depot.lat,
        "lon": depot.lon,
    }