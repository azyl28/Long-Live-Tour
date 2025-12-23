"""
Data model for a Fueling Log entry.
"""
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class FuelingLog:
    """Represents a fueling event for a vehicle."""
    id: int = field(init=False)
    vehicle_id: int
    fueling_time: datetime
    mileage_at_fueling: float
    liters_added: float
    trip_id: int | None = None
    price_per_liter: float | None = None
    total_cost: float | None = None
    notes: str | None = None
