"""
Builds a persistent mapping between LTA SpeedBand road segments
and OSM graph edges.

Run this whenever the Singapore graph is rebuilt.

Output

cache/
    speed_band_mapping.json
"""

from pathlib import Path
import json

import osmnx as ox

from services.lta_service import LTADataMallClient
from ingestion.speed_bands import SpeedBandService
from services.traffic.road_matcher import RoadMatcher


GRAPH_PATH = Path("cache/singapore.graphml")
OUTPUT_PATH = Path("cache/speed_band_mapping.json")


def main():

    ###############################################################
    # Load graph
    ###############################################################

    print("[*] Loading graph...")

    graph = ox.load_graphml(
        GRAPH_PATH,
    )

    ###############################################################
    # Download speed band geometry
    ###############################################################

    print("[*] Downloading speed bands...")

    client = LTADataMallClient()

    service = SpeedBandService(client)

    speed_bands = service.fetch()

    print(f"[*] {len(speed_bands)} speed bands downloaded.")

    ###############################################################
    # Build mapping
    ###############################################################

    matcher = RoadMatcher()

    mapping = {}

    matched = 0

    for i, band in enumerate(speed_bands, start=1):

        if i % 100 == 0:
            print(f"[*] Processed {i}/{len(speed_bands)} speed bands")

        edge = matcher.nearest_edge(
            graph,
            band.start_lat,
            band.start_lon,
        )

        #
        # Skip if we couldn't match
        #

        if edge is None:
            continue

        mapping[str(band.link_id)] = {
            "edges": [
                list(edge),
            ],
            "road_name": getattr(
                band,
                "road_name",
                None,
            ),
            "direction": getattr(
                band,
                "direction",
                None,
            ),
        }

        matched += 1

    ###############################################################
    # Save
    ###############################################################

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(
            OUTPUT_PATH,
            "w",
    ) as f:

        json.dump(
            mapping,
            f,
            indent=4,
        )

    ###############################################################

    print(f"[+] Matched {matched}/{len(speed_bands)} speed bands.")

    print(f"[+] Mapping saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()