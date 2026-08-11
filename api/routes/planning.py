# api/routes/planning.py

from fastapi import APIRouter

from services.world.world_manager import world_manager

router = APIRouter(
    prefix="/api/planning",
    tags=["planning"],
)


@router.get("")
async def get_planning():
    world = world_manager.get_world()

    return {
        "summary": world.summary,
        "recommend_replan": world.recommend_replan,
        "assessments": world.assessments,
        "routes": world.routes,
    }