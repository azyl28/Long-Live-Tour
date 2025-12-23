"""
Data model for a Trip (Road Card).
"""
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class Trip:
    """Represents a trip record in the system."""
    id: int # FIX: Made 'id' a regular constructor argument
    vehicle_id: int
    driver_id: int
    start_time: datetime
    # Inherited from the vehicle at the moment of creation
    start_mileage: float
    start_fuel: float
    route: str
    purpose: str
    road_card_number: str | None = None
    end_time: datetime | None = None
    end_mileage: float | None = None
    end_fuel: float | None = None
    # Calculated upon completion
    distance: float | None = None
    fuel_consumed_calculated: float | None = None
    # 'active', 'completed', 'cancelled'
    status: str = "active"
    notes: str | None = None
