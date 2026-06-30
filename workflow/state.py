# workflow/state.py

from typing import TypedDict
from models.world_state import WorldState


class WorkflowState(TypedDict):
    world: WorldState
