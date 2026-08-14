from __future__ import annotations

from typing import Any
import osmnx as ox
import requests

from services.world.world_manager import world_manager


ONEMAP_SEARCH_URL = (
    "https://www.onemap.gov.sg/api/common/elastic/search"
)


def geocode_location(
    location: str,
) -> dict[str, Any]:
    """
    Resolve a human-readable Singapore location into coordinates.

    This tool is intended for cases where the agent or another tool
    cannot resolve a location directly.

    It does not:
    - create an order
    - modify WorldState
    - assign a vehicle
    - create a route

    Returns:
        {
            "success": True,
            "query": "...",
            "location": "...",
            "latitude": ...,
            "longitude": ...,
            "confidence": "...",
            "candidates": [...]
        }
    """

    if not location or not location.strip():
        return {
            "success": False,
            "error": "Location was empty.",
        }

    query = location.strip()

    try:
        response = requests.get(
            ONEMAP_SEARCH_URL,
            params={
                "searchVal": query,
                "returnGeom": "Y",
                "getAddrDetails": "Y",
                "pageNum": 1,
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

    except requests.RequestException as exc:

        return {
            "success": False,
            "error": f"Geocoding service unavailable: {exc}",
        }

    results = data.get("results", [])

    if not results:

        return {
            "success": False,
            "query": query,
            "error": (
                f"Could not find a location matching '{query}'."
            ),
        }

    candidates = []

    for result in results[:5]:

        try:
            latitude = float(result["LATITUDE"])
            longitude = float(result["LONGITUDE"])
        except (KeyError, TypeError, ValueError):
            continue

        candidates.append(
            {
                "name": result.get(
                    "SEARCHVAL",
                    query,
                ),
                "address": result.get(
                    "ADDRESS",
                ),
                "latitude": latitude,
                "longitude": longitude,
                "building": result.get(
                    "BUILDING",
                ),
                "postal_code": result.get(
                    "POSTAL",
                ),
            }
        )

    if not candidates:

        return {
            "success": False,
            "query": query,
            "error": (
                "The geocoder returned results, "
                "but none contained valid coordinates."
            ),
        }

    # OneMap generally returns the most relevant result first.
    best = candidates[0]

    return {
        "success": True,
        "query": query,
        "location": best["name"],
        "address": best["address"],
        "latitude": best["latitude"],
        "longitude": best["longitude"],
        "confidence": "best_match",
        "candidates": candidates,
    }

async def geocode_order(order_id: str):
    world = world_manager.get_world()

    order = next(
        (
            o for o in world.new_orders
            if o.order_id == order_id
        ),
        None,
    )

    if order is None:
        return {
            "success": False,
            "error": f"Order {order_id} not found.",
        }

    # --------------------------------------------------
    # Pickup
    # --------------------------------------------------

    if order.pickup_lat is None or order.pickup_lon is None:
        pickup = geocode_location(order.pickup_address)

        if not pickup["success"]:
            return {
                "success": False,
                "order_id": order_id,
                "error": f"Could not geocode pickup: {order.pickup_address}",
            }

        order.pickup_lat = pickup["latitude"]
        order.pickup_lon = pickup["longitude"]

    # --------------------------------------------------
    # Delivery
    # --------------------------------------------------

    if order.delivery_lat is None or order.delivery_lon is None:
        delivery = geocode_location(order.delivery_address)

        if not delivery["success"]:
            return {
                "success": False,
                "order_id": order_id,
                "error": f"Could not geocode delivery: {order.delivery_address}",
            }

        order.delivery_lat = delivery["latitude"]
        order.delivery_lon = delivery["longitude"]

    # --------------------------------------------------
    # Snap to OSM graph
    # --------------------------------------------------

    order.pickup_node = ox.distance.nearest_nodes(
        world.graph,
        X=order.pickup_lon,
        Y=order.pickup_lat,
    )

    order.delivery_node = ox.distance.nearest_nodes(
        world.graph,
        X=order.delivery_lon,
        Y=order.delivery_lat,
    )

    return {
        "success": True,
        "order_id": order_id,
        "pickup": {
            "lat": order.pickup_lat,
            "lon": order.pickup_lon,
            "node": order.pickup_node,
        },
        "delivery": {
            "lat": order.delivery_lat,
            "lon": order.delivery_lon,
            "node": order.delivery_node,
        },
    }