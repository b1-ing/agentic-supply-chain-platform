# services/osm_service.py

import osmnx as ox


class OSMService:

    def load_graph(self, place: str):

        return ox.graph_from_place(
            place,
            network_type="drive"
        )