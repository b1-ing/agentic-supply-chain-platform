class GraphBuilder:
    def apply_constraints(self, graph, constraints):
        for constraint in constraints:
            for u, v, k in constraint["edges"]:
                edge = graph[u][v][k]

                # 1. Base Setup: Enforce that live travel time is the baseline cost
                live_travel_time = edge.get("travel_time", 1.0)

                # If routing_cost hasn't been initialized yet, baseline it to live traffic
                if "routing_cost" not in edge:
                    edge["routing_cost"] = live_travel_time

                # 2. Hard Constraints (Always Override)
                # If a road is closed, live travel time is irrelevant. It must be infinity.
                if constraint["closed"]:
                    edge["routing_cost"] = float("inf")
                    edge["closed"] = True
                    continue

                # 3. Soft Constraints (Smart Layering to prevent Double-Charging)
                # Estimate what the total cost *should* be based on incident severity
                estimated_minimum_cost = live_travel_time + constraint["penalty"]

                # If the live_travel_time is ALREADY worse than our estimate,
                # the data feed has already "charged" the fleet. Do not add the penalty.
                if live_travel_time >= estimated_minimum_cost:
                    # Live data has caught up with the incident. Do nothing.
                    continue
                else:
                    # Live data hasn't caught up yet (lag), or the incident is worse
                    # than the flow reflects. Set the cost to our conservative estimate.
                    edge["routing_cost"] = estimated_minimum_cost

        return graph


def graph_node(state: dict) -> dict:
    # 1. Safely pull your dataclass out of the LangGraph state wrapper
    world = state["world"]

    # 2. Instantiate your GraphBuilder engine
    builder = GraphBuilder()

    # 3. Pass the objects living inside the world state directly into the builder.
    # Note: NetworkX modifies the graph object in-place.
    world.graph = builder.apply_constraints(
        world.graph,
        world.constraints
    )

    # 4. Return the updated world object back into the state channel
    return {"world": world}

    return state