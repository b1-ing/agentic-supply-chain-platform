from models.vehicles.vehicle import Vehicle


class StandardTruck(Vehicle):
    max_weight_kg: float = 5000

    height_m: float = 3.5
    width_m: float = 2.5
    length_m: float = 8.0
