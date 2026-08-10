"""
Build a persistent mapping between LTA SpeedBand road segments
and OSM graph edges.

Run this whenever the Singapore OSM graph is rebuilt.

Output:
    cache/
        speed_band_mapping.json
"""

import json
import time
from pathlib import Path

import osmnx as ox

from services.lta_service import LTADataMallClient
from ingestion.speed_bands import SpeedBandService
from services.traffic.road_matcher import RoadMatcher


GRAPH_PATH = Path("cache/singapore.graphml")
OUTPUT_PATH = Path("cache/speed_band_mapping.json")


def main():

    ####################################################################
    # Load OSM graph
    ####################################################################

    print("[*] Loading Singapore OSM graph...")

    start = time.perf_counter()

    graph = ox.load_graphml(
        GRAPH_PATH,
    )

    graph_load_time = time.perf_counter() - start

    print(
        f"[+] Graph loaded in "
        f"{graph_load_time:.2f}s"
    )

    print(
        f"[+] Graph contains "
        f"{graph.number_of_nodes():,} nodes and "
        f"{graph.number_of_edges():,} edges"
    )

    ####################################################################
    # Download ALL LTA speed bands
    ####################################################################

    print("\n[*] Downloading LTA SpeedBands...")

    start = time.perf_counter()

    client = LTADataMallClient()

    service = SpeedBandService(
        client,
    )

    speed_bands = service.fetch()

    download_time = time.perf_counter() - start

    print(
        f"[+] Downloaded "
        f"{len(speed_bands):,} LTA speed bands "
        f"in {download_time:.2f}s"
    )

    ####################################################################
    # Build STRtree
    ####################################################################

    print("\n[*] Building OSM spatial index...")

    matcher = RoadMatcher()

    start = time.perf_counter()

    matcher.build_index(
        graph,
    )

    index_time = time.perf_counter() - start

    print(
        f"[+] STRtree built in "
        f"{index_time:.2f}s"
    )

    ####################################################################
    # Match ALL LTA segments
    ####################################################################

    print(
        f"\n[*] Matching "
        f"{len(speed_bands):,} LTA segments "
        f"onto OSM..."
    )

    start = time.perf_counter()

    mapping = {}

    matched = 0
    missed = 0

    total = len(speed_bands)

    for i, band in enumerate(
        speed_bands,
        start=1,
    ):

        edge = matcher.nearest_edge(
            graph,
            band.start_lat,
            band.start_lon,
        )

        ############################################################
        # No match
        ############################################################

        if edge is None:

            missed += 1

            print(
                f"[MISS] "
                f"LTA {band.link_id} "
                f"({band.start_lat:.6f}, "
                f"{band.start_lon:.6f})"
            )

            continue

        ############################################################
        # Successful match
        ############################################################

        matched += 1

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

        ############################################################
        # Progress
        ############################################################

        if (
            i % 100 == 0
            or i == total
        ):

            elapsed = (
                time.perf_counter()
                - start
            )

            rate = (
                i / elapsed
                if elapsed > 0
                else 0
            )

            remaining = (
                total - i
            )

            eta = (
                remaining / rate
                if rate > 0
                else 0
            )

            print(
                f"[{i:,}/{total:,}] "
                f"matched={matched:,} "
                f"missed={missed:,} "
                f"rate={rate:.1f}/s "
                f"ETA={eta:.1f}s"
            )

    matching_time = (
        time.perf_counter()
        - start
    )

    ####################################################################
    # Save mapping
    ####################################################################

    print("\n[*] Saving mapping...")

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    start = time.perf_counter()

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            mapping,
            f,
            indent=2,
        )

    save_time = (
        time.perf_counter()
        - start
    )

    ####################################################################
    # Summary
    ####################################################################

    print("\n========================================")
    print("       SPEED BAND MAPPING RESULTS")
    print("========================================")

    print(
        f"LTA segments       : {total:,}"
    )

    print(
        f"Matched            : {matched:,}"
    )

    print(
        f"Missed             : {missed:,}"
    )

    print(
        f"Match rate         : "
        f"{(matched / total * 100):.2f}%"
        if total
        else "Match rate         : N/A"
    )

    print(
        f"Graph load         : "
        f"{graph_load_time:.2f}s"
    )

    print(
        f"LTA download       : "
        f"{download_time:.2f}s"
    )

    print(
        f"STRtree build      : "
        f"{index_time:.2f}s"
    )

    print(
        f"Spatial matching   : "
        f"{matching_time:.2f}s"
    )

    print(
        f"Mapping save       : "
        f"{save_time:.2f}s"
    )

    print(
        f"Total preprocessing: "
        f"{graph_load_time + download_time + index_time + matching_time + save_time:.2f}s"
    )

    print(
        f"\n[+] Mapping saved to:"
        f"\n    {OUTPUT_PATH}"
    )

    print("========================================")


if __name__ == "__main__":
    main()