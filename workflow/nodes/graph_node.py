def graph_node(state):

    builder = GraphBuilder()

    state["graph"] = builder.apply(

        state["graph"],

        state["constraints"]

    )

    return state