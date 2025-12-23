"""
GUI Window for managing Trips.

This module is responsible for the user interface for starting and ending trips.
It interacts with the service layer to perform all business logic, ensuring
that the GUI remains decoupled from the database and core rules.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QComboBox, QFormLayout, QGroupBox, QDateTimeEdit,
    QDoubleSpinBox, QLineEdit, QTextEdit, QSplitter,
    QInputDialog
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont, QColor
from pathlib import Path

from ..services.trip_service import TripService
from ..services.vehicle_service import VehicleService
from ..services.driver_service import DriverService
from ..models.vehicle import Vehicle

class TripWindow(QWidget):
    """The main window for trip management."""

    def __init__(self, db_path: Path):
        super().__init__()
        self.db_path = db_path

        # Initialize the service layer
        self.vehicle_service = VehicleService(self.db_path)
        self.trip_service = TripService(self.db_path, self.vehicle_service)
        self.driver_service = DriverService(self.db_path)

        self.selected_vehicle: Vehicle | None = None

        self.setup_ui()
        self.load_initial_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        header = QLabel("🚗 Trip Management")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # --- Left Panel: New Trip Form ---
        form_widget = QGroupBox("Start a New Trip")
        form_layout = QFormLayout(form_widget)

        self.vehicle_combo = QComboBox()
        self.vehicle_combo.currentIndexChanged.connect(self.on_vehicle_selected)
        form_layout.addRow("Vehicle:", self.vehicle_combo)

        self.driver_combo = QComboBox()
        form_layout.addRow("Driver:", self.driver_combo)

        # Display-only fields for vehicle state
        self.start_mileage_label = QLabel("Select a vehicle")
        self.start_fuel_label = QLabel("Select a vehicle")
        form_layout.addRow("Start Mileage:", self.start_mileage_label)
        form_layout.addRow("Start Fuel:", self.start_fuel_label)

        self.route_input = QLineEdit()
        self.route_input.setPlaceholderText("e.g., Warsaw -> Krakow")
        form_layout.addRow("Route:", self.route_input)

        self.purpose_input = QLineEdit()
        self.purpose_input.setPlaceholderText("e.g., Client meeting")
        form_layout.addRow("Purpose:", self.purpose_input)

        self.start_trip_button = QPushButton("🚀 Start Trip")
        self.start_trip_button.clicked.connect(self.start_trip)
        form_layout.addRow(self.start_trip_button)

        splitter.addWidget(form_widget)

        # --- Right Panel: Active Trips Table ---
        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        table_header = QLabel("Active and Recent Trips")
        self.trips_table = QTableWidget()
        self.trips_table.setColumnCount(7)
        self.trips_table.setHorizontalHeaderLabels([
            "ID", "Vehicle", "Driver", "Start Time",
            "Start Mileage", "Status", "Actions"
        ])
        self.trips_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.trips_table.setEditTriggers(QTableWidget.NoEditTriggers)

        table_layout.addWidget(table_header)
        table_layout.addWidget(self.trips_table)
        splitter.addWidget(table_widget)

    def load_initial_data(self):
        """Loads drivers and available vehicles into the form."""
        try:
            # Load active drivers
            active_drivers = self.driver_service.get_all_active_drivers()
            self.driver_combo.clear()
            for driver in active_drivers:
                self.driver_combo.addItem(f"{driver.first_name} {driver.last_name}", driver.id)

            # Load available vehicles
            available_vehicles = self.vehicle_service.get_all_vehicles(status_filter='available')
            self.vehicle_combo.clear()
            for vehicle in available_vehicles:
                self.vehicle_combo.addItem(
                    f"{vehicle.registration_number} ({vehicle.brand} {vehicle.model})",
                    vehicle.id
                )

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load initial data: {e}")

    def on_vehicle_selected(self, index):
        """Updates the display labels when a vehicle is selected."""
        if index == -1:
            self.selected_vehicle = None
            self.start_mileage_label.setText("Select a vehicle")
            self.start_fuel_label.setText("Select a vehicle")
            return

        vehicle_id = self.vehicle_combo.currentData()
        self.selected_vehicle = self.vehicle_service.get_vehicle_by_id(vehicle_id)

        if self.selected_vehicle:
            self.start_mileage_label.setText(f"{self.selected_vehicle.current_mileage:.1f} km")
            self.start_fuel_label.setText(f"{self.selected_vehicle.current_fuel:.1f} L")
        else:
            self.start_mileage_label.setText("Error: Vehicle not found")
            self.start_fuel_label.setText("Error: Vehicle not found")

    def start_trip(self):
        """Handles the 'Start Trip' button click."""
        if not self.selected_vehicle or self.driver_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Validation Error", "Please select a vehicle and a driver.")
            return

        vehicle_id = self.selected_vehicle.id
        driver_id = self.driver_combo.currentData()
        route = self.route_input.text()
        purpose = self.purpose_input.text()

        if not route or not purpose:
            QMessageBox.warning(self, "Validation Error", "Route and purpose cannot be empty.")
            return

        try:
            new_trip = self.trip_service.start_new_trip(vehicle_id, driver_id, route, purpose)
            if new_trip:
                QMessageBox.information(self, "Success", f"Trip #{new_trip.id} started successfully!")
                self.load_initial_data() # Refresh vehicle list
                self.refresh_trips_table()
            else:
                QMessageBox.critical(self, "Error", "Could not start the trip. The vehicle may no longer be available.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")

    def refresh_trips_table(self):
        """Reloads the data in the trips table."""
        try:
            self.trips_table.setRowCount(0)
            all_trips = self.trip_service.get_all_trips()

            # For simplicity, we create dictionaries to avoid multiple lookups in a loop
            vehicles = {v.id: v for v in self.vehicle_service.get_all_vehicles()}
            drivers = {d.id: d for d in self.driver_service.get_all_active_drivers()} # Assuming get_all_active_drivers is sufficient

            for row, trip in enumerate(all_trips):
                self.trips_table.insertRow(row)

                vehicle = vehicles.get(trip.vehicle_id)
                driver = drivers.get(trip.driver_id)

                vehicle_name = f"{vehicle.registration_number}" if vehicle else "N/A"
                driver_name = f"{driver.first_name} {driver.last_name}" if driver else "N/A"

                self.trips_table.setItem(row, 0, QTableWidgetItem(str(trip.id)))
                self.trips_table.setItem(row, 1, QTableWidgetItem(vehicle_name))
                self.trips_table.setItem(row, 2, QTableWidgetItem(driver_name))
                self.trips_table.setItem(row, 3, QTableWidgetItem(str(trip.start_time)))
                self.trips_table.setItem(row, 4, QTableWidgetItem(str(trip.start_mileage)))
                self.trips_table.setItem(row, 5, QTableWidgetItem(trip.status))

                # Add "End Trip" button for active trips
                if trip.status == 'active':
                    end_trip_button = QPushButton("✅ End Trip")
                    end_trip_button.clicked.connect(lambda _, t=trip.id: self.end_trip(t))
                    self.trips_table.setCellWidget(row, 6, end_trip_button)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to refresh trips table: {e}")

    def end_trip(self, trip_id: int):
        """Handles the 'End Trip' button click from the table."""
        trip = self.trip_service.get_trip_by_id(trip_id)
        if not trip:
            QMessageBox.critical(self, "Error", "Trip not found.")
            return

        end_mileage, ok = QInputDialog.getDouble(
            self,
            "End Trip",
            f"Enter end mileage for trip #{trip.id} (current: {trip.start_mileage} km):",
            trip.start_mileage,
            trip.start_mileage,
            1_000_000,
            1,
        )
        if not ok:
            return

        end_fuel, ok = QInputDialog.getDouble(
            self,
            "End Trip",
            f"Enter end fuel for trip #{trip.id} (start: {trip.start_fuel} L):",
            trip.start_fuel,
            0,
            1_000,
            1,
        )
        if not ok:
            return

        try:
            completed_trip = self.trip_service.complete_trip(trip_id, end_mileage, end_fuel)
            if completed_trip:
                QMessageBox.information(self, "Success", f"Trip #{completed_trip.id} completed successfully!")
                self.load_initial_data()
                self.refresh_trips_table()
            else:
                QMessageBox.critical(self, "Error", "Could not complete the trip.")
        except ValueError as ve:
            QMessageBox.warning(self, "Validation Error", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {e}")
