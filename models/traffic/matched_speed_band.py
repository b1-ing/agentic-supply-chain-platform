from dataclasses import dataclass

from models.speed_band import SpeedBand


@dataclass
class MatchedSpeedBand:
    speed_band: SpeedBand

    affected_edges: list[tuple[int, int, int]]

    confidence: float = 1.0

    matched_road: str | None = None

    direction: str | None = None
