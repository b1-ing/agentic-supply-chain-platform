# workflow/nodes/context_node.py


def context_node(state):

    world = state["world"]

    context = []

    for event in world.matched_events:
        context.append(
            {
                "type": event["incident"].incident_type,
                "message": event["incident"].message,
                "edges": event["edges"],
            }
        )

    world.context = context

    return {"world": world}
