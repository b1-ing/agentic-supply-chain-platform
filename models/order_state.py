from dataclasses import dataclass
from typing import Optional

from models.order import Order
from models.world_state import WorldState


@dataclass
class OrderState:

    # Original user input
    raw_order: str

    # Parsed order
    order: Optional[Order] = None

    # Shared system state
    world: Optional[WorldState] = None

    # Optional diagnostics
    extraction_reasoning: Optional[str] = None

    validation_errors: list[str] = None