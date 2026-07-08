from models.vehicle import Vehicle


class StandardTruck(Vehicle):
    max_weight_kg: float = 5000
    max_volume_m3: float = 25
    max_pallets: int = 10

    height_m: float = 3.5
    width_m: float = 2.5
    length_m: float = 8.0
