from typing import Literal

from pydantic import BaseModel


class PlanningDecision(BaseModel):
    """
    Decision returned by the Planning Decision Agent.

    This determines whether the optimisation pipeline should
    be executed and, if so, how broadly.
    """

    # Required
    should_replan: bool

    # Optional
    scope: (
        Literal[
            "none",
            "single_vehicle",
            "partial",
            "global",
        ]
        | None
    ) = None

    affected_vehicles: list[str] | None = None

    objective: str | None = None

    reason: str | None = None

    summary: str | None = None
