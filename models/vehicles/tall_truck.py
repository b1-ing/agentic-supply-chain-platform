from models.vehicles.vehicle import Vehicle
from pygments.lexers import q


class TallTruck(Vehicle):
    max_weight_kg: float = 10000

    height_m: float = 6.0
    width_m: float = 2.5
    length_m: float = 10.0

    hazardous_certified: bool = False
