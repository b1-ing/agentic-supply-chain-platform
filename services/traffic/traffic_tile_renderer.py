from pathlib import Path

import math
import io

import networkx as nx
import matplotlib.pyplot as plt
from PIL import Image


class TrafficTileRenderer:

    def __init__(
            self,
            graph: nx.MultiDiGraph,
            tile_dir: str = "cache/traffic_tiles",
    ):
        self.graph = graph
        self.tile_dir = Path(tile_dir)

    ####################################################################
    # Coordinate conversion
    ####################################################################

    @staticmethod
    def lonlat_to_pixel(
            lon,
            lat,
            zoom,
            tile_size=256,
    ):
        """
        Convert WGS84 longitude/latitude to global Web Mercator pixels.
        """

        lat = max(
            min(lat, 85.05112878),
            -85.05112878,
        )

        scale = tile_size * (2 ** zoom)

        x = (
                (lon + 180.0)
                / 360.0
                * scale
        )

        lat_rad = math.radians(lat)

        y = (
                (
                        1
                        - math.asinh(
                    math.tan(lat_rad)
                )
                        / math.pi
                )
                / 2
                * scale
        )

        return x, y

    ####################################################################
    # Render tile
    ####################################################################

    def render_tile(
            self,
            z: int,
            x: int,
            y: int,
    ):
        """
        Render one 256x256 XYZ raster tile.
        """

        tile_size = 256

        image = Image.new(
            "RGBA",
            (
                tile_size,
                tile_size,
            ),
            (
                0,
                0,
                0,
                0,
            ),
        )

        # Global pixel bounds of this tile
        min_x = x * tile_size
        min_y = y * tile_size

        max_x = (
                (x + 1)
                * tile_size
        )

        max_y = (
                (y + 1)
                * tile_size
        )

        fig = plt.figure(
            figsize=(2.56, 2.56),
            dpi=100,
        )

        ax = fig.add_axes(
            [0, 0, 1, 1]
        )

        ax.set_xlim(
            min_x,
            max_x,
        )

        ax.set_ylim(
            max_y,
            min_y,
        )

        ax.axis("off")

        for u, v, key, data in self.graph.edges(
                keys=True,
                data=True,
        ):

            geometry = data.get(
                "geometry"
            )

            if geometry is None:

                u_data = self.graph.nodes[u]
                v_data = self.graph.nodes[v]

                coordinates = [
                    (
                        u_data["x"],
                        u_data["y"],
                    ),
                    (
                        v_data["x"],
                        v_data["y"],
                    ),
                ]

            else:

                coordinates = list(
                    geometry.coords
                )

            pixels = [
                self.lonlat_to_pixel(
                    lon,
                    lat,
                    z,
                    tile_size,
                )
                for lon, lat in coordinates
            ]

            # Skip edges nowhere near this tile
            if not pixels:
                continue

            px = [p[0] for p in pixels]
            py = [p[1] for p in pixels]

            if (
                    max(px) < min_x
                    or min(px) > max_x
                    or max(py) < min_y
                    or min(py) > max_y
            ):
                continue

            # Convert global → tile-local pixels
            local_x = [
                value - min_x
                for value in px
            ]

            local_y = [
                value - min_y
                for value in py
            ]

            traffic_ratio = data.get(
                "traffic_ratio"
            )

            if traffic_ratio is None:
                color = "#94a3b8"

            elif traffic_ratio >= 0.8:
                color = "#22c55e"

            elif traffic_ratio >= 0.6:
                color = "#eab308"

            elif traffic_ratio >= 0.4:
                color = "#f97316"

            else:
                color = "#ef4444"

            ax.plot(
                local_x,
                local_y,
                color=color,
                linewidth=1.5,
                solid_capstyle="round",
            )

        buffer = io.BytesIO()

        fig.savefig(
            buffer,
            format="png",
            transparent=True,
            dpi=100,
        )

        plt.close(fig)

        buffer.seek(0)

        return Image.open(buffer).convert(
            "RGBA"
        )