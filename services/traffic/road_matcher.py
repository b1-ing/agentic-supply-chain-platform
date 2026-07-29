# services/traffic/road_matcher.py

from __future__ import annotations

import osmnx as ox


class RoadMatcher:
    """
    Maps real-world traffic events onto the OSM road network.

    Responsibilities
    ----------------
    - Find the nearest road edge to an event.
    - Convert traffic events into matched graph events.
    """

    ####################################################################
    # Edge lookup
    ####################################################################

    def nearest_edge(
            self,
            graph,
            lat: float,
            lon: float,
    ) -> tuple[int, int, int]:
        """
        Returns the nearest OSM edge (u, v, key)
        to a latitude/longitude coordinate.
        """

        return ox.distance.nearest_edges(
            graph,
            X=lon,
            Y=lat,
        )

    ####################################################################
    # Generic matcher
    ####################################################################

    def _match(
            self,
            graph,
            events,
            lat_attr: str,
            lon_attr: str,
    ) -> list[dict]:
        """
        Generic matcher used by all traffic event types.
        """

        matched = []

        for event in events:

            lat = getattr(event, lat_attr)
            lon = getattr(event, lon_attr)

            edge = self.nearest_edge(
                graph,
                lat,
                lon,
            )

            matched.append(
                {
                    "event": event,
                    "edge": edge,
                }
            )

        return matched

    ####################################################################
    # Traffic incidents
    ####################################################################

    def match_incidents(
            self,
            graph,
            incidents,
    ) -> list[dict]:

        return self._match(
            graph,
            incidents,
            lat_attr="latitude",
            lon_attr="longitude",
        )

    ####################################################################
    # Roadworks
    ####################################################################

    def match_roadworks(
            self,
            graph,
            roadworks,
    ) -> list[dict]:

        return self._match(
            graph,
            roadworks,
            lat_attr="latitude",
            lon_attr="longitude",
        )

    ####################################################################
    # Speed bands
    ####################################################################

    def match_speed_bands(
            self,
            graph,
            speed_bands,
    ) -> list[dict]:
        """
        Speed bands represent road segments rather than points.

        For now, match using the segment's start coordinate.
        Later this can be upgraded to spatial line matching.
        """

        return self._match(
            graph,
            speed_bands,
            lat_attr="start_lat",
            lon_attr="start_lon",
        )