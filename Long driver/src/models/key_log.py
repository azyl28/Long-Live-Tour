# -*- coding: utf-8 -*-
"""
Model pojazdu z rozszerzonym wsparciem dla current_fuel i statusów
"""
import sqlite3
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Vehicle:
    """Model pojazdu z pełną obsługą paliwa i statusów"""
    id: Optional[int] = None
    registration_number: str = ""
    brand: str = ""
    model: str = ""
    fuel_type: str = "Benzyna"
    fuel_consumption: float = 7.5  # L/100km
    current_mileage: float = 0.0
    current_fuel: float = 50.0     # NOWE POLE - aktualny stan paliwa
    status: str = "available"      # available, inuse, service, broken
    tank_capacity: Optional[float] = None
    vin: Optional[str] = None
    production_year: int = 2020
    notes: str = ""
    created_at: Optional[str] = None

    def calculate_fuel_usage(self, distance_km: float) -> float:
        """Oblicza zużycie paliwa na podstawie średniego spalania"""
        return (distance_km * self.fuel_consumption) / 100.0

    def is_available_for_checkout(self) -> bool:
        """Sprawdza czy pojazd może być wypożyczony"""
        return self.status == "available"

    def update_after_trip(self, end_mileage: float, end_fuel: float) -> None:
        """Aktualizuje pojazd po zakończonej trasie"""
        self.current_mileage = end_mileage
        self.current_fuel = end_fuel
        self.status = "available"

class VehicleRepository:
    """Repozytorium pojazdów - operacje CRUD"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """Pobiera połączenie z bazą"""
        return sqlite3.connect(self.db_path)

    def create_vehicle(self, vehicle: Vehicle) -> bool:
        """Tworzy nowy pojazd"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vehicles 
                (registration_number, brand, model, fuel_type, fuel_consumption, 
                 current_mileage, current_fuel, status, tank_capacity, vin, 
                 production_year, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                vehicle.registration_number.upper().strip(),
                vehicle.brand.strip(),
                vehicle.model.strip(),
                vehicle.fuel_type,
                vehicle.fuel_consumption,
                vehicle.current_mileage,
                vehicle.current_fuel,
                vehicle.status,
                vehicle.tank_capacity,
                vehicle.vin,
                vehicle.production_year,
                vehicle.notes.strip()
            ])
            conn.commit()
            vehicle.id = cursor.lastrowid
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def update_vehicle(self, vehicle: Vehicle) -> bool:
        """Aktualizuje pojazd"""
        if not vehicle.id:
            return False
            
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vehicles SET 
                registration_number=?, brand=?, model=?, fuel_type=?,
                fuel_consumption=?, current_mileage=?, current_fuel=?,
                status=?, tank_capacity=?, vin=?, production_year=?, notes=?
                WHERE id=?
            """, [
                vehicle.registration_number.upper().strip(),
                vehicle.brand.strip(),
                vehicle.model.strip(),
                vehicle.fuel_type,
                vehicle.fuel_consumption,
                vehicle.current_mileage,
                vehicle.current_fuel,
                vehicle.status,
                vehicle.tank_capacity,
                vehicle.vin,
                vehicle.production_year,
                vehicle.notes.strip(),
                vehicle.id
            ])
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete_vehicle(self, vehicle_id: int) -> bool:
        """Usuwa pojazd"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM vehicles WHERE id=?", (vehicle_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_vehicle(self, vehicle_id: int) -> Optional[Vehicle]:
        """Pobiera pojazd po ID"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, registration_number, brand, model, fuel_type,
                       fuel_consumption, current_mileage, current_fuel,
                       status, tank_capacity, vin, production_year, notes, created_at
                FROM vehicles WHERE id=?
            """, (vehicle_id,))
            row = cursor.fetchone()
            if row:
                return Vehicle(*row)
            return None
        finally:
            conn.close()

    def get_all_vehicles(self, status_filter: str = None) -> List[Vehicle]:
        """Pobiera wszystkie pojazdy z opcjonalnym filtrem statusu"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            query = """
                SELECT id, registration_number, brand, model, fuel_type,
                       fuel_consumption, current_mileage, current_fuel,
                       status, tank_capacity, vin, production_year, notes, created_at
                FROM vehicles
            """
            params = []
            
            if status_filter:
                query += " WHERE status=?"
                params.append(status_filter)
                
            query += " ORDER BY registration_number"
            cursor.execute(query, params)
            
            vehicles = []
            for row in cursor.fetchall():
                vehicles.append(Vehicle(*row))
            return vehicles
        finally:
            conn.close()

    def get_available_vehicles(self) -> List[Vehicle]:
        """Pobiera tylko dostępne pojazdy"""
        return self.get_all_vehicles("available")

    def checkout_vehicle(self, vehicle_id: int, mileage: float, fuel: float) -> bool:
        """Wypożycza pojazd - zmienia status na inuse"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vehicles 
                SET status='inuse', current_mileage=?, current_fuel=?
                WHERE id=? AND status='available'
            """, (mileage, fuel, vehicle_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def return_vehicle(self, vehicle_id: int, mileage: float, fuel: float) -> bool:
        """Zwrot pojazdu - zmienia status na available"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vehicles 
                SET status='available', current_mileage=?, current_fuel=?
                WHERE id=?
            """, (mileage, fuel, vehicle_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
