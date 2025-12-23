"""
Service layer for managing the state of vehicles.

This service is the single point of authority for any changes to a vehicle's
mileage, fuel, or status. It ensures that all operations are valid
and that the vehicle's state remains consistent.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from models.vehicle import Vehicle

class VehicleService:
    """Manages business logic for vehicles."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """Establishes a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_vehicle_by_id(self, vehicle_id: int) -> Vehicle | None:
        """Retrieves a single vehicle by its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM vehicles WHERE id = ?", (vehicle_id,))
            row = cursor.fetchone()
            if row:
                return Vehicle(**dict(row))
        return None

    def get_all_vehicles(self, status_filter: str | None = None) -> list[Vehicle]:
        """
        Retrieves all vehicles, optionally filtering by status.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            query = "SELECT * FROM vehicles ORDER BY registration_number"
            params = []
            if status_filter:
                query = "SELECT * FROM vehicles WHERE status = ? ORDER BY registration_number"
                params.append(status_filter)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [Vehicle(**dict(row)) for row in rows]

    def update_vehicle_state_for_trip_start(self, vehicle_id: int) -> bool:
        """
        Updates a vehicle's status to 'in_trip' when a trip starts.
        This is an atomic operation to prevent race conditions.
        Returns True if the update was successful, False otherwise.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE vehicles
                SET status = 'in_trip', last_updated = ?
                WHERE id = ? AND status = 'available'
                """,
                (datetime.now(), vehicle_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def update_vehicle_state_for_trip_end(
        self, vehicle_id: int, end_mileage: float, end_fuel: float
    ) -> bool:
        """
        Updates a vehicle's mileage, fuel, and status to 'available'
        when a trip is completed. This is the primary way a vehicle's
        state is updated.
        """
        vehicle = self.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehicle not found.")
        if end_mileage < vehicle.current_mileage:
            raise ValueError("End mileage cannot be less than the current mileage.")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE vehicles
                SET current_mileage = ?, current_fuel = ?, status = 'available', last_updated = ?
                WHERE id = ? AND status = 'in_trip'
                """,
                (end_mileage, end_fuel, datetime.now(), vehicle_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def add_fuel_to_vehicle(
        self, vehicle_id: int, liters_added: float, mileage_at_fueling: float
    ) -> bool:
        """
        Updates a vehicle's fuel level and mileage after a fueling event.
        This is the only sanctioned way to increase a vehicle's fuel.
        """
        vehicle = self.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehicle not found.")
        if mileage_at_fueling < vehicle.current_mileage:
            raise ValueError("Mileage at fueling cannot be less than current mileage.")

        new_fuel_level = vehicle.current_fuel + liters_added
        if vehicle.tank_capacity and new_fuel_level > vehicle.tank_capacity:
            # Maybe just warn instead of raising an error
            print(f"Warning: Fuel level ({new_fuel_level}L) exceeds tank capacity ({vehicle.tank_capacity}L).")

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE vehicles
                SET current_mileage = ?, current_fuel = ?, last_updated = ?
                WHERE id = ?
                """,
                (mileage_at_fueling, new_fuel_level, datetime.now(), vehicle_id),
            )
            conn.commit()
            return cursor.rowcount > 0
