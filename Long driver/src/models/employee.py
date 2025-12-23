"""
Model pracownika
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Employee:
    """Klasa reprezentująca pracownika"""
    id: Optional[int] = None
    first_name: str = ""
    last_name: str = ""
    position: str = ""
    permissions: str = "pracownik"  # pracownik, kierownik, administrator
    is_active: bool = True
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """Walidacja danych"""
        if not self.first_name or not self.last_name:
            raise ValueError("Imię i nazwisko są wymagane")
        if self.permissions not in ["pracownik", "kierownik", "administrator"]:
            raise ValueError("Nieprawidłowe uprawnienia")
    
    @property
    def full_name(self) -> str:
        """Zwraca pełne imię i nazwisko"""
        return f"{self.first_name} {self.last_name}"
    
    def can_checkout_vehicle(self) -> bool:
        """Sprawdza czy pracownik może pobrać pojazd"""
        return self.is_active and self.permissions in ["pracownik", "kierownik", "administrator"]
    
    def can_manage_vehicles(self) -> bool:
        """Sprawdza czy pracownik może zarządzać pojazdami"""
        return self.permissions in ["kierownik", "administrator"]
    
    def to_dict(self) -> dict:
        """Konwertuje do słownika"""
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'full_name': self.full_name,
            'position': self.position,
            'permissions': self.permissions,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }