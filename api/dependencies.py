from models.world.world_state import WorldState
from services.world.world_manager import world_manager


def get_world() -> WorldState:
    return world_manager.get_world()