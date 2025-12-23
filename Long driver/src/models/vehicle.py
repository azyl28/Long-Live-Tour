"""
Data model for a Vehicle.
"""
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Vehicle:
    """Represents a vehicle in the system, holding its current state."""
    id: int  # FIX: Made 'id' a regular constructor argument
    registration_number: str
    brand: str
    model: str
    normative_consumption: float  # l/100km
    vin: str | None = None
    production_year: int | None = None
    fuel_type: str = "Diesel"
    tank_capacity: float | None = None
    # The single source of truth for the vehicle's current state
    current_mileage: float = 0.0
    current_fuel: float = 0.0
    # 'available', 'in_trip', or 'maintenance'
    status: str = "available"
    last_updated: datetime = field(default_factory=datetime.now)
