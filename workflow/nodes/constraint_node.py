PENALTIES = {"LOW": 25, "MEDIUM": 100, "HIGH": 300, "CRITICAL": 1000}


def constraint_node(state):

    world = state["world"]

    constraints = []

    for assessment, matched in zip(world.assessments, world.matched_events):
        constraints.append(
            {
                "edges": matched["edges"],
                "penalty": PENALTIES[assessment.severity],
                "closed": assessment.road_status.value == "CLOSED",
            }
        )

    world.constraints = constraints

    return {"world": world}
