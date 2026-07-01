from enum import Enum
from pydantic import BaseModel


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RoadStatus(str, Enum):
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    CLOSED = "CLOSED"


class IncidentAssessment(BaseModel):
    incident_index: int
    severity: Severity
    road_status: RoadStatus
    expected_delay_minutes: int
    affects_routing: bool
    reason: str


class PlanningResult(BaseModel):
    assessments: list[IncidentAssessment]
    recommend_replan: bool
    summary: str
