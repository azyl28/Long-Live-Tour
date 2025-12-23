# -*- coding: utf-8 -*-
"""
Model trasy z automatycznym obliczaniem zużycia paliwa
"""
import sqlite3
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Trip:
    """Model przejazdu z pełną obsługą paliwa"""
    id: Optional[int] = None
    vehicle_id: int = 0
    employee_id: int = 0
    key_log_id: Optional[int] = None
    start_date: str = ""
    end_date: Optional[str] = None
    start_mileage: Optional[float] = None
    end_mileage: Optional[float] = None
    distance: Optional[float] = None
    start_fuel: Optional[float] = None
    end_fuel: Optional[float] = None
    fuel_used: Optional[float] = None
    calculated_fuel: Optional[float] = None  # NOWE - przeliczone wg spalania
    purpose: str = ""
    ordered_by: str = ""
    status: str = "active"  # active, completed
    vehicle_ok: bool = True
    notes: str = ""

    @property
    def is_active(self) -> bool:
        """Czy trasa aktywna"""
        return self.status == "active" and self.end_date is None

    def calculate_distance(self) -> Optional[float]:
        """Oblicza dystans"""
        if self.start_mileage is not None and self.end_mileage is not None:
            return self.end_mileage - self.start_mileage
        return None

    def calculate_fuel_used(self) -> Optional[float]:
        """Rzeczywiste zużycie paliwa"""
        if self.start_fuel is not None and self.end_fuel is not None:
            return self.start_fuel - self.end_fuel
        return None

class TripRepository:
    """Repozytorium przejazdów"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def create_trip(self, trip: Trip) -> bool:
        """Rozpoczyna nową trasę"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO trips 
                (vehicle_id, employee_id, key_log_id, start_date, start_mileage, 
                 start_fuel, purpose, ordered_by, status, vehicle_ok, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                trip.vehicle_id,
                trip.employee_id,
                trip.key_log_id,
                trip.start_date,
                trip.start_mileage,
                trip.start_fuel,
                trip.purpose.strip(),
                trip.ordered_by.strip(),
                trip.status,
                1 if trip.vehicle_ok else 0,
                trip.notes.strip()
            ])
            conn.commit()
            trip.id = cursor.lastrowid
            return True
        finally:
            conn.close()

    def complete_trip(self, trip_id: int, end_mileage: float, end_fuel: float, 
                     vehicle_consumption: float) -> Optional[Trip]:
        """Zakończa trasę z automatycznym przeliczaniem paliwa"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            
            # Pobierz dane startowe
            cursor.execute("""
                SELECT vehicle_id, start_mileage, start_fuel, purpose, ordered_by, notes
                FROM trips WHERE id=?
            """, (trip_id,))
            start_data = cursor.fetchone()
            if not start_data:
                return None
                
            vehicle_id, start_mileage, start_fuel, purpose, ordered_by, notes = start_data
            
            # Oblicz wszystko
            distance = end_mileage - (start_mileage or 0)
            fuel_used = (start_fuel or 0) - end_fuel
            calculated_fuel = (distance * vehicle_consumption) / 100.0
            
            # Aktualizuj trasę
            cursor.execute("""
                UPDATE trips SET 
                end_date=?, end_mileage=?, distance=?, end_fuel=?,
                fuel_used=?, calculated_fuel=?, status='completed'
                WHERE id=?
            """, (
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                end_mileage, distance, end_fuel,
                fuel_used, calculated_fuel, trip_id
            ))
            
            # Aktualizuj pojazd
            cursor.execute("""
                UPDATE vehicles SET 
                current_mileage=?, current_fuel=?, status='available'
                WHERE id=?
            """, (end_mileage, end_fuel, vehicle_id))
            
            conn.commit()
            return Trip(id=trip_id, end_mileage=end_mileage, end_fuel=end_fuel,
                       distance=distance, fuel_used=fuel_used, 
                       calculated_fuel=calculated_fuel)
        finally:
            conn.close()

    def get_active_trips_for_vehicle(self, vehicle_id: int) -> List[Trip]:
        """Pobiera aktywne trasy dla pojazdu"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, vehicle_id, employee_id, key_log_id, start_date,
                       start_mileage, start_fuel, purpose, ordered_by, status, notes
                FROM trips 
                WHERE vehicle_id=? AND status='active'
                ORDER BY start_date DESC
            """, (vehicle_id,))
            
            trips = []
            for row in cursor.fetchall():
                trips.append(Trip(*row))
            return trips
        finally:
            conn.close()

    def get_all_trips(self, status_filter: str = None) -> List[Trip]:
        """Pobiera wszystkie trasy"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT id, vehicle_id, employee_id, key_log_id, start_date, end_date,
                       start_mileage, end_mileage, distance, start_fuel, end_fuel,
                       fuel_used, calculated_fuel, purpose, ordered_by, status, notes
                FROM trips
            """
            params = []
            if status_filter:
                query += " WHERE status=?"
                params.append(status_filter)
            query += " ORDER BY start_date DESC"
            
            cursor.execute(query, params)
            trips = []
            for row in cursor.fetchall():
                trips.append(Trip(*row))
            return trips
        finally:
            conn.close()


if __name__ == "__main__":
    db_path = Path(__file__).parent.parent.parent / "database" / "fleet.db"
    repo = TripRepository(db_path)
    print("Model trasy gotowy!")
