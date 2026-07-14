from routing import matrix_service, route_builder, or_tools_solver




@traceable(name="Planning Node")
def planning_node(state):

    world = state["world"]

    problem = problem_builder.build(world)

    matrix = matrix_service.build(
        world,
        problem.locations,
    )

    routes = or_tools_solver.solve(
        matrix=matrix.matrix,
        starts=problem.starts,
        ends=problem.ends,
        demands=problem.demands,
        capacities=problem.capacities,
    )

    world.routes = route_builder.build(
        world,
        matrix,
        world.vehicles,
        routes,
    )

    return {"world": world}