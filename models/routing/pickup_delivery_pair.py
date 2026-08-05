from dataclasses import dataclass



@dataclass(slots=True)
class PickupDeliveryPair:
    order_id: str
    pickup: int
    delivery: int
    allowed_vehicles: list[int]