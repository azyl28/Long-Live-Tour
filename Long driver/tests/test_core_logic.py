"""
Tests for the core business logic of the fleet management system.

These tests ensure that the service layer correctly enforces the rules
of the system, such as state transitions and data integrity.
"""
import unittest
import sqlite3
from pathlib import Path
from datetime import datetime
from services.vehicle_service import VehicleService
from services.trip_service import TripService
from models.vehicle import Vehicle

class TestCoreLogic(unittest.TestCase):
    """Test suite for the core application logic."""

    def setUp(self):
        """
        Set up a temporary, in-memory database for each test.
        """
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row # FIX: Enable dictionary-like row access
        self.db_path = Path(":memory:")
        self.create_schema()

        # Re-initialize services for each test to ensure isolation
        self.vehicle_service = VehicleService(self.db_path)
        self.vehicle_service.get_connection = lambda: self.conn

        self.trip_service = TripService(self.db_path, self.vehicle_service)
        self.trip_service.get_connection = lambda: self.conn

    def tearDown(self):
        """
        Close the database connection after each test.
        """
        self.conn.close()

    def create_schema(self):
        """
        Create the database schema directly for test reliability.
        """
        with self.conn as c:
            c.execute("""
                CREATE TABLE vehicles (
                    id INTEGER PRIMARY KEY,
                    registration_number TEXT NOT NULL, brand TEXT NOT NULL, model TEXT NOT NULL,
                    normative_consumption REAL NOT NULL, current_mileage REAL NOT NULL,
                    current_fuel REAL NOT NULL, status TEXT NOT NULL, last_updated TEXT,
                    vin TEXT, production_year INTEGER, fuel_type TEXT, tank_capacity REAL
                );
            """)
            c.execute("""
                CREATE TABLE trips (
                    id INTEGER PRIMARY KEY, vehicle_id INTEGER NOT NULL, driver_id INTEGER NOT NULL,
                    start_time TEXT NOT NULL, start_mileage REAL NOT NULL, start_fuel REAL NOT NULL,
                    route TEXT NOT NULL, purpose TEXT, status TEXT NOT NULL, road_card_number TEXT,
                    end_time TEXT, end_mileage REAL, end_fuel REAL,
                    distance REAL, fuel_consumed_calculated REAL, notes TEXT
                );
            """)

    def test_start_trip_inherits_vehicle_state_and_updates_status(self):
        """
        Verify that starting a trip correctly updates the vehicle's status
        and that the trip inherits the correct starting mileage and fuel.
        """
        # 1. Arrange: Create a vehicle with a known state
        initial_mileage = 50000.5
        initial_fuel = 35.0
        with self.conn as c:
            c.execute(
                """
                INSERT INTO vehicles (
                    id, registration_number, brand, model, current_mileage,
                    current_fuel, status, normative_consumption
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (1, "TEST-123", "Ford", "Transit", initial_mileage, initial_fuel, "available", 7.5)
            )

        # 2. Act: Start a new trip with this vehicle
        new_trip = self.trip_service.start_new_trip(
            vehicle_id=1,
            driver_id=101,
            route="Test Route",
            purpose="Test Purpose"
        )

        # 3. Assert: Check the results
        self.assertIsNotNone(new_trip)

        # Assert that the trip inherited the correct state
        self.assertEqual(new_trip.start_mileage, initial_mileage)
        self.assertEqual(new_trip.start_fuel, initial_fuel)

        # Assert that the vehicle's status was updated
        updated_vehicle = self.vehicle_service.get_vehicle_by_id(1)
        self.assertIsNotNone(updated_vehicle)
        self.assertEqual(updated_vehicle.status, "in_trip")

    def test_complete_trip_updates_vehicle_state(self):
        """
        Verify that completing a trip correctly updates the vehicle's master state
        (mileage and fuel) and sets its status back to 'available'.
        """
        # 1. Arrange: Create a vehicle and start a trip with it
        initial_mileage = 50000.0
        initial_fuel = 40.0
        with self.conn as c:
            c.execute(
                """
                INSERT INTO vehicles (id, registration_number, brand, model, current_mileage, current_fuel, status, normative_consumption)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (1, "TEST-123", "Ford", "Transit", initial_mileage, initial_fuel, "available", 8.0)
            )

        trip = self.trip_service.start_new_trip(1, 101, "Test", "Test")
        self.assertEqual(self.vehicle_service.get_vehicle_by_id(1).status, "in_trip")

        # 2. Act: Complete the trip
        end_mileage = 50200.0
        end_fuel = 24.0 # 200km at 8L/100km = 16L used. 40 - 16 = 24.
        completed_trip = self.trip_service.complete_trip(trip.id, end_mileage, end_fuel)

        # 3. Assert: Check the results
        self.assertIsNotNone(completed_trip)
        self.assertEqual(completed_trip.status, "completed")
        self.assertEqual(completed_trip.end_mileage, end_mileage)

        # Assert that the vehicle's master state is now updated
        updated_vehicle = self.vehicle_service.get_vehicle_by_id(1)
        self.assertIsNotNone(updated_vehicle)
        self.assertEqual(updated_vehicle.status, "available")
        self.assertEqual(updated_vehicle.current_mileage, end_mileage)
        self.assertEqual(updated_vehicle.current_fuel, end_fuel)

if __name__ == '__main__':
    unittest.main()
