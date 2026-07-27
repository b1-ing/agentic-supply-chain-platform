from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class PenaltySource(str, Enum):
    """
    Where the penalty originated.
    """

    LTA = "lta"
    WEB = "web"
    WEATHER = "weather"
    MANUAL = "manual"
    LLM = "llm"


class PenaltyType(str, Enum):
    """
    What kind of disruption this represents.
    """

    ACCIDENT = "accident"
    CONGESTION = "congestion"
    ROADWORKS = "roadworks"
    ROAD_CLOSURE = "road_closure"
    FLOOD = "flood"
    EVENT = "event"
    BREAKDOWN = "breakdown"
    UNKNOWN = "unknown"


@dataclass
class TrafficPenalty:
    """
    Represents one traffic-related penalty.

    This object never modifies the graph directly.
    Instead, it is attached to affected edges and the
    TrafficPenaltyService computes the final travel time.
    """

    #
    # Identity
    #

    penalty_id: str

    source: PenaltySource

    penalty_type: PenaltyType

    #
    # Severity
    #

    severity: float
    """
    Normalised between 0 and 1.
    """

    #
    # Penalty behaviour
    #

    additional_seconds: float = 0.0
    """
    Delay introduced by this incident.
    """

    multiplier: float = 1.0
    """
    Maximum multiplicative increase this
    incident is allowed to contribute.
    """

    radius_m: float = 0.0
    """
    Radius of influence.

    0 means only the matched road.
    """

    decay_m: float = 150.0
    """
    Controls how quickly penalties decay
    with distance.
    """

    #
    # Lifetime
    #

    created_at: Optional[datetime] = None

    expires_at: Optional[datetime] = None

    #
    # Metadata
    #

    description: Optional[str] = None


@dataclass
class EdgePenalty:
    """
    Represents the effect of a TrafficPenalty
    on one specific edge.
    """

    penalty_id: str

    edge_u: int

    edge_v: int

    distance_from_incident: float

    additional_seconds: float

    multiplier: float


@dataclass
class EdgePenalty:
    edge: tuple[int, int, int]

    incident_id: str

    additional_seconds: float

    multiplier: float
