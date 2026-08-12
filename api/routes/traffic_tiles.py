from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from services.world.world_manager import world_manager
from services.traffic.traffic_tile_renderer import (
    TrafficTileRenderer,
)


router = APIRouter(
    prefix="/traffic",
    tags=["traffic"],
)

_renderer = None


def get_renderer():

    global _renderer

    world = world_manager.get_world()

    if _renderer is None:
        _renderer = TrafficTileRenderer(world.graph)

    return _renderer


@router.get("/{z}/{x}/{y}.png")
async def get_traffic_tile(
    z: int,
    x: int,
    y: int,
):

    if z < 13 or z > 20:
        raise HTTPException(
            status_code=400,
            detail="Invalid zoom level",
        )

    renderer = get_renderer()

    image = renderer.render_tile(
        z=z,
        x=x,
        y=y,
    )

    from io import BytesIO

    buffer = BytesIO()

    image.save(
        buffer,
        format="PNG",
    )

    return Response(
        content=buffer.getvalue(),
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=30",
        },
    )
