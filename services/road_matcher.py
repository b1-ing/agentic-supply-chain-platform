# services/road_matcher.py

import osmnx as ox


class RoadMatcher:
    def __init__(self, graph):

        self.graph = graph

    def nearest_edge(self, lat: float, lon: float):

        edge = ox.distance.nearest_edges(self.graph, X=lon, Y=lat)

        return edge

    def nearby_edges(self, lat: float, lon: float, radius: float = 100):
        """
        TODO
        Version 1:
            return nearest edge

        Version 2:
            return every edge
            within radius
        """

        return [self.nearest_edge(lat, lon)]
