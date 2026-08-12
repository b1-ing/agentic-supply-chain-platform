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

        scale = tile_size * (2**zoom)

        x = (lon + 180.0) / 360.0 * scale

        lat_rad = math.radians(lat)

        y = (1 - math.asinh(math.tan(lat_rad)) / math.pi) / 2 * scale

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

        # Global pixel bounds of this tile
        min_x = x * tile_size
        min_y = y * tile_size
        max_x = (x + 1) * tile_size
        max_y = (y + 1) * tile_size

        fig = plt.figure(
            figsize=(2.56, 2.56),
            dpi=100,
        )
        ax = fig.add_axes([0, 0, 1, 1])

        # FIX: Set the axis limits to local tile dimensions
        ax.set_xlim(0, tile_size)
        ax.set_ylim(tile_size, 0)
        ax.axis("off")

        for u, v, key, data in self.graph.edges(keys=True, data=True):
            geometry = data.get("geometry")

            if geometry is None:
                u_data = self.graph.nodes[u]
                v_data = self.graph.nodes[v]
                coordinates = [
                    (u_data["x"], u_data["y"]),
                    (v_data["x"], v_data["y"]),
                ]
            else:
                geometry = wkt.loads(geometry)
                coordinates = list(geometry.coords)

            pixels = [
                self.lonlat_to_pixel(float(lon), float(lat), z, tile_size)
                for lon, lat in coordinates
            ]

            if not pixels:
                continue

            px = [p[0] for p in pixels]
            py = [p[1] for p in pixels]

            # Bounding box check using global pixels
            if max(px) < min_x or min(px) > max_x or max(py) < min_y or min(py) > max_y:
                continue

            # Convert global → tile-local pixels (correctly maps to 0-256 bounds)
            local_x = [value - min_x for value in px]
            local_y = [value - min_y for value in py]

            traffic_ratio = data.get("traffic_ratio")
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

        return Image.open(buffer).convert("RGBA")

    # ============================================================
    # TEST: Render one Singapore traffic tile
    # ============================================================

    def lonlat_to_tile(self, lon, lat, zoom):
        """
        Convert WGS84 coordinates to XYZ tile coordinates.
        """
        n = 2**zoom

        x = int((lon + 180.0) / 360.0 * n)

        lat_rad = math.radians(lat)

        y = int((1 - math.asinh(math.tan(lat_rad)) / math.pi) / 2 * n)

        return x, y


# import networkx as nx
# from shapely import wkt
# graph = nx.read_graphml("cache/singapore.graphml")
#
# # Create renderer
# renderer = TrafficTileRenderer(
#     graph=graph,
#     tile_dir="cache/traffic_tiles",
# )
#
#
# # Approximate centre of Singapore
# singapore_lon = 103.8198
# singapore_lat = 1.3521
#
# # Try zoom 13 first
# zoom = 13
#
# tile_x, tile_y = renderer.lonlat_to_tile(
#     singapore_lon,
#     singapore_lat,
#     zoom,
# )
#
# print(
#     f"Singapore tile at z={zoom}: "
#     f"x={tile_x}, y={tile_y}"
# )
#
#
#
#
# # Render the tile
# tile = renderer.render_tile(
#     z=zoom,
#     x=tile_x,
#     y=tile_y,
# )
#
#
# # Save it
# output_path = Path(
#     f"cache/traffic_tile_{zoom}_{tile_x}_{tile_y}.png"
# )
#
# output_path.parent.mkdir(
#     parents=True,
#     exist_ok=True,
# )
#
# tile.save(output_path)
#
# print(
#     f"Saved tile to: "
#     f"{output_path.resolve()}"
# )
#
