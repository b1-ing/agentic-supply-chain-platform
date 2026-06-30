# engine/constraint_engine.py

from models.constraints import RoutingConstraint, ConstraintAction


class ConstraintEngine:
    def __init__(self, matcher):

        self.matcher = matcher

    def process_event(self, event):

        edges = self.matcher.nearby_edges(event.latitude, event.longitude)

        if event.event_type.value == "roadwork":
            return RoutingConstraint(
                id=event.event_id or "unknown",
                action=ConstraintAction.PENALIZE,
                affected_edges=edges,
                value=300,
                start=event.timestamp,
                end=None,
                confidence=0.95,
                reason="Roadwork",
                metadata={},
            )

        return None
