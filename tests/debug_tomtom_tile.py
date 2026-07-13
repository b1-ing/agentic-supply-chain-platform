"""
Debug helper: dump raw TomTom features from a single tile so you can see
what the API is actually returning.

Usage:
    python debug_tomtom_tile.py                  # default: a CBD-ish tile
    python debug_tomtom_tile.py 807 508          # specific (x, y) at zoom 10
    python debug_tomtom_tile.py 807 508 --no-cache
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

from services.tomtom_service import TomTomTileService


def main():
    x = int(sys.argv[1]) if len(sys.argv) > 1 else 807
    y = int(sys.argv[2]) if len(sys.argv) > 2 else 508

    if "--no-cache" in sys.argv:
        os.environ["TOMTOM_CACHE_DISABLED"] = "1"

    s = TomTomTileService()
    segments = s.fetch_single_tile(x, y)

    print(f"\n=== Tile {s.zoom}/{x}/{y}: {len(segments)} features ===\n")

    if not segments:
        print("(empty — HTTP 204, decode failure, or 200 with no features)")
        return

    # Sort by traffic_level descending so the worst offenders are at the top
    segments_sorted = sorted(
        segments, key=lambda seg: seg["traffic_level"], reverse=True
    )

    bands = {
        "free (0)": 0,
        "light (0-0.15)": 0,
        "mid (0.15-0.40)": 0,
        "heavy (0.40-0.80)": 0,
        "max (0.80-1.0)": 0,
        "closed": 0,
    }
    for seg in segments_sorted:
        tl = seg["traffic_level"]
        if seg["closed"]:
            bands["closed"] += 1
        elif tl >= 0.80:
            bands["max (0.80-1.0)"] += 1
        elif tl >= 0.40:
            bands["heavy (0.40-0.80)"] += 1
        elif tl >= 0.15:
            bands["mid (0.15-0.40)"] += 1
        elif tl > 0:
            bands["light (0-0.15)"] += 1
        else:
            bands["free (0)"] += 1

    print("Band distribution:")
    for band, count in bands.items():
        print(f"  {band:<20} {count}")
    print()

    print("Top 20 features by traffic_level:")
    for i, seg in enumerate(segments_sorted[:20], 1):
        geom = seg["geometry"]
        if geom is not None and hasattr(geom, "bounds"):
            minx, miny, maxx, maxy = geom.bounds
            midx, midy = (minx + maxx) / 2, (miny + maxy) / 2
            loc = f"({midx:.4f}, {midy:.4f})"
        else:
            loc = "(no geometry)"
        flag = "CLOSED" if seg["closed"] else "     "
        print(
            f"  {i:>2}. [{flag}] traffic_level={seg['traffic_level']:.3f}  center={loc}"
        )


if __name__ == "__main__":
    main()
