# services/traffic/speed_band_mapping.py

from pathlib import Path
import json


class SpeedBandMapping:
    def __init__(
        self,
        path="cache/speed_band_mapping.json",
    ):

        with open(path) as f:
            self.mapping = json.load(f)

    def get_edges(
        self,
        link_id,
    ):

        record = self.mapping.get(str(link_id))

        if record is None:
            return []

        return [tuple(edge) for edge in record["edges"]]
