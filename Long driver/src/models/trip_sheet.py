"""
Model karty drogowej (SM-102)
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional

@dataclass
class TripSheet:
    """Karta drogowa SM-102"""
    id: Optional[int] = None
    key_log_id: int = 0
    sheet_number: str = ""
    date: Optional[date] = None
    status: str = "otwarta"  # otwarta, zamknięta, archiwum
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Walidacja danych"""
        if self.status not in ["otwarta", "zamknięta", "archiwum"]:
            raise ValueError("Nieprawidłowy status karty")
        if self.date is None:
            self.date = date.today()
    
    @property
    def is_open(self) -> bool:
        """Sprawdza czy karta jest otwarta"""
        return self.status == "otwarta"
    
    def to_dict(self) -> dict:
        """Konwertuje do słownika"""
        return {
            'id': self.id,
            'key_log_id': self.key_log_id,
            'sheet_number': self.sheet_number,
            'date': self.date.isoformat() if self.date else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }