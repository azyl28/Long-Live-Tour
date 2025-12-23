from dataclasses import dataclass

@dataclass
class Vehicle:
    id: int
    name: str
    registration_number: str
    status: str
    mileage: float
    fuel_consumption: float
