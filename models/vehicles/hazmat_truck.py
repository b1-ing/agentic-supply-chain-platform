from models.vehicles.vehicle import Vehicle


class HazmatTruck(Vehicle):
    max_weight_kg: float = 10000
    max_volume_m3: float = 35
    max_pallets: int = 16

    height_m: float = 4.0
    width_m: float = 2.5
    length_m: float = 10.0

    hazardous_certified: bool = True
