import networkx as nx


class RoutingService:

    def build(
            self,
            world,
            ordered_nodes,
    ):

        complete_path = []

        total_time = 0

        for source, target in zip(
                ordered_nodes[:-1],
                ordered_nodes[1:],
        ):

            path = nx.shortest_path(
                world.graph,
                source,
                target,
                weight="travel_time",
            )

            travel_time = nx.shortest_path_length(
                world.graph,
                source,
                target,
                weight="travel_time",
            )

            complete_path.extend(path[:-1])

            total_time += travel_time

        complete_path.append(ordered_nodes[-1])

        return {
            "path": complete_path,
            "travel_time": total_time,
        }