from pydantic import BaseModel


class RoutePointResponse(BaseModel):
    sequence: int

    lat: float
    lon: float

    kind: str

    order_id: str | None = None

    vehicle_id: str | None = None


class RouteSegmentResponse(BaseModel):
    geometry: list[list[float]]

    distance_m: float
    travel_time_seconds: float


class RouteResponse(BaseModel):
    route_id: str | None = None
    vehicle_id: str

    stops: list[RoutePointResponse]

    segments: list[RouteSegmentResponse]

    total_distance_m: float
    total_travel_time_seconds: float
