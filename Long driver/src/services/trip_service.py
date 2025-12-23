"""
Service layer for managing the trip lifecycle.

This service coordinates with the VehicleService to ensure that trips
are started and completed in a way that maintains data integrity.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from models.trip import Trip
from services.vehicle_service import VehicleService

class TripService:
    """Manages business logic for trips."""

    def __init__(self, db_path: Path, vehicle_service: VehicleService):
        self.db_path = db_path
        self.vehicle_service = vehicle_service

    def get_connection(self) -> sqlite3.Connection:
        """Establishes a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_trip_by_id(self, trip_id: int) -> Trip | None:
        """Retrieves a single trip by its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
            row = cursor.fetchone()
            if row:
                return Trip(**dict(row))
        return None

    def get_all_trips(self, limit: int = 50) -> list[Trip]:
        """
        Retrieves all trips, newest first, with a limit.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM trips ORDER BY start_time DESC LIMIT ?", (limit,))
            rows = cursor.fetchall()
            return [Trip(**dict(row)) for row in rows]

    def start_new_trip(
        self, vehicle_id: int, driver_id: int, route: str, purpose: str
    ) -> Trip | None:
        """
        Starts a new trip. This is a crucial transactional operation.
        """
        vehicle = self.vehicle_service.get_vehicle_by_id(vehicle_id)
        if not vehicle:
            raise ValueError("Vehicle not found.")
        if vehicle.status != 'available':
            raise ValueError("Vehicle is not available for a new trip.")

        # Transaction: Update vehicle status and create trip record together.
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # 1. Update vehicle status to 'in_trip'
                updated = self.vehicle_service.update_vehicle_state_for_trip_start(vehicle_id)
                if not updated:
                    raise Exception("Failed to reserve vehicle for the trip.")

                # 2. Create the new trip record with the vehicle's current state
                start_time = datetime.now()
                cursor.execute(
                    """
                    INSERT INTO trips (
                        vehicle_id, driver_id, start_time, start_mileage,
                        start_fuel, route, purpose, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
                    """,
                    (
                        vehicle_id,
                        driver_id,
                        start_time,
                        vehicle.current_mileage,
                        vehicle.current_fuel,
                        route,
                        purpose,
                    ),
                )
                trip_id = cursor.lastrowid
                conn.commit()

                return self.get_trip_by_id(trip_id)

            except Exception as e:
                conn.rollback()
                # Revert vehicle status if trip creation failed
                self.vehicle_service.update_vehicle_state_for_trip_end(
                    vehicle_id, vehicle.current_mileage, vehicle.current_fuel
                )
                raise e

    def complete_trip(
        self, trip_id: int, end_mileage: float, end_fuel: float, notes: str | None = None
    ) -> Trip | None:
        """
        Completes an active trip. This is another crucial transactional operation.
        """
        trip = self.get_trip_by_id(trip_id)
        if not trip:
            raise ValueError("Trip not found.")
        if trip.status != 'active':
            raise ValueError("Trip is not active and cannot be completed.")

        # Calculations
        distance = end_mileage - trip.start_mileage
        vehicle = self.vehicle_service.get_vehicle_by_id(trip.vehicle_id)
        fuel_consumed = (distance / 100) * vehicle.normative_consumption if vehicle else None

        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                # 1. Update the trip record
                cursor.execute(
                    """
                    UPDATE trips
                    SET end_time = ?, end_mileage = ?, end_fuel = ?,
                        distance = ?, fuel_consumed_calculated = ?,
                        status = 'completed', notes = ?
                    WHERE id = ?
                    """,
                    (
                        datetime.now(),
                        end_mileage,
                        end_fuel,
                        distance,
                        fuel_consumed,
                        notes,
                        trip_id,
                    ),
                )

                # 2. Update the vehicle's master state
                self.vehicle_service.update_vehicle_state_for_trip_end(
                    trip.vehicle_id, end_mileage, end_fuel
                )
                conn.commit()
                return self.get_trip_by_id(trip_id)

            except Exception as e:
                conn.rollback()
                raise e
