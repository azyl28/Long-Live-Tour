"""
Data model for a Driver.
"""
from dataclasses import dataclass, field
from datetime import date

@dataclass
class Driver:
    """Represents a driver in the system."""
    id: int = field(init=False)
    first_name: str
    last_name: str
    license_number: str
    license_category: str
    license_expiry: date
    phone_number: str | None = None
    status: str = "active"
