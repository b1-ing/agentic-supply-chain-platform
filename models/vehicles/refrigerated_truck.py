from models.vehicles.vehicle import Vehicle


class RefrigeratedTruck(Vehicle):
    max_weight_kg: float = 20000

    height_m: float = 4.5
    width_m: float = 2.5
    length_m: float = 12.0

    refrigerated: bool = True
