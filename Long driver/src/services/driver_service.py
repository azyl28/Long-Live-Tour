"""
Service layer for managing drivers.
"""
import sqlite3
from pathlib import Path
from models.driver import Driver
from typing import List

class DriverService:
    """Manages business logic for drivers."""

    def __init__(self, db_path: Path):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """Establishes a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_all_active_drivers(self) -> List[Driver]:
        """
        Retrieves a list of all drivers with an 'active' status.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drivers WHERE status = 'active' ORDER BY last_name, first_name")
            rows = cursor.fetchall()
            return [Driver(**dict(row)) for row in rows]

    def get_driver_by_id(self, driver_id: int) -> Driver | None:
        """
        Retrieves a single driver by their ID.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM drivers WHERE id = ?", (driver_id,))
            row = cursor.fetchone()
            if row:
                return Driver(**dict(row))
        return None

    def create_driver(self, driver: Driver) -> Driver:
        """
        Adds a new driver to the system.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO drivers (first_name, last_name, license_number, license_category, license_expiry, phone_number, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    driver.first_name,
                    driver.last_name,
                    driver.license_number,
                    driver.license_category,
                    driver.license_expiry,
                    driver.phone_number,
                    driver.status,
                ),
            )
            driver.id = cursor.lastrowid
            conn.commit()
            return driver

    def update_driver(self, driver: Driver) -> bool:
        """
        Updates an existing driver's information.
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE drivers
                SET first_name = ?, last_name = ?, license_number = ?,
                    license_category = ?, license_expiry = ?, phone_number = ?, status = ?
                WHERE id = ?
                """,
                (
                    driver.first_name,
                    driver.last_name,
                    driver.license_number,
                    driver.license_category,
                    driver.license_expiry,
                    driver.phone_number,
                    driver.status,
                    driver.id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0
