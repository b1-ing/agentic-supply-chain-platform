import pytest

from app.initialise import initialise_world
from services.world.world_manager import world_manager


@pytest.fixture(scope="session", autouse=True)
def setup_world():
    initialise_world()


@pytest.fixture(autouse=True)
def reset_operational_state():
    world_manager.reset()