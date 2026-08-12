from fastapi import APIRouter

from services.world.world_manager import world_manager
import osmnx as ox

router = APIRouter(
    prefix="/world",
    tags=["world"],
)


@router.get("/graph")
def get_graph():
    world = world_manager.get_world()

    geojson = ox.graph_to_gdfs(
        world.graph,
        nodes=False,
        fill_edge_geometry=True,
    ).to_json()

    import json

    return json.loads(geojson)
