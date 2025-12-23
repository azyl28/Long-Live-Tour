from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RoadCard:
    id: int
    vehicle_id: int
    employee_id: int
    status: str
    start_mileage: float
    start_date: str
    end_mileage: Optional[float] = None
    end_date: Optional[str] = None
