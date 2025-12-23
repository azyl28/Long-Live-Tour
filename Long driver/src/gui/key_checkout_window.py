# -*- coding: utf-8 -*-
"""
Okno wydania kluczyków - BLOKADA DUPLIKATU + WALIDACJA PRZEBIEGU
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QDateTimeEdit, QDoubleSpinBox, QLineEdit, QTextEdit, QMessageBox,
    QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, QDateTime
from PySide6.QtGui import QFont
import sqlite3
from pathlib import Path

class KeyCheckoutWindow(QWidget):
    """Okno wydawania kluczyków do pojazdu."""
    
    def __init__(self):
        super().__init__()
        self.db_path = Path(__file__).parent.parent.parent / "database" / "fleet.db"
        self.selected_vehicle_tank = 0
        self.setup_ui()
        self.load_employees()
        self.load_vehicles()

    # ==========================
    # UI
    # ==========================

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        header = QLabel("🔑 Wydanie kluczyka / pobranie pojazdu")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        form_group = QGroupBox("Dane wydania")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)
        main_layout.addWidget(form_group)

        # Debug pracowników
        self.employee_count_label = QLabel("Pracownicy: 0")
        form_layout.addRow(self.employee_count_label)

        self.employee_combo = QComboBox()
        self.employee_combo.setPlaceholderText("Wybierz pracownika / kierowcę")
        form_layout.addRow("Pracownik:", self.employee_combo)

        self.vehicle_combo = QComboBox()
        self.vehicle_combo.setPlaceholderText("Wybierz DOSTĘPNY pojazd")
        self.vehicle_combo.currentIndexChanged.connect(self.on_vehicle_selected)
        form_layout.addRow("Pojazd:", self.vehicle_combo)

        self.checkout_dt = QDateTimeEdit()
        self.checkout_dt.setCalendarPopup(True)
        self.checkout_dt.setDateTime(QDateTime.currentDateTime())
        form_layout.addRow("Data i godzina wydania:", self.checkout_dt)

        self.checkout_mileage = QDoubleSpinBox()
        self.checkout_mileage.setRange(0, 1_000_000)
        self.checkout_mileage.setDecimals(1)
        self.checkout_mileage.setSuffix(" km")
        self.checkout_mileage.setToolTip("Auto-wypełni ostatni przebieg pojazdu")
        form_layout.addRow("Ostatni przebieg:", self.checkout_mileage)

        self.checkout_fuel = QDoubleSpinBox()
        self.checkout_fuel.setRange(0, 500)
        self.checkout_fuel.setDecimals(1)
        self.checkout_fuel.setSuffix(" L")
        self.checkout_fuel.valueChanged.connect(self.validate_fuel_tank)
        self.checkout_fuel.setToolTip("Auto-wypełni ostatni stan paliwa pojazdu")
        form_layout.addRow("Stan paliwa:", self.checkout_fuel)

        # Info o baku
        self.tank_info_label = QLabel("Pojemność baku: -- L")
        form_layout.addRow("🔥 Pojemność baku:", self.tank_info_label)

        self.storage_location = QLineEdit()
        self.storage_location.setPlaceholderText("Np. Szafka A3, hak 5")
        form_layout.addRow("Miejsce klucza:", self.storage_location)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Dodatkowe informacje o stanie pojazdu, uwagi itp.")
        form_layout.addRow("Uwagi:", self.notes)

        # Przyciski
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.refresh_button = QPushButton("🔄 Odśwież")
        self.refresh_button.clicked.connect(self.refresh_lists)
        buttons_layout.addWidget(self.refresh_button)

        self.checkout_button = QPushButton("✅ Wydaj kluczyk")
        self.checkout_button.clicked.connect(self.checkout_key)
        buttons_layout.addWidget(self.checkout_button)

        self.close_button = QPushButton("Zamknij")
        self.close_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_button)

        main_layout.addLayout(buttons_layout)

    # ==========================
    # AUTO-WYPEŁNIANIE po wyborze pojazdu
    # ==========================

    def on_vehicle_selected(self, index):
        """AUTO-WYPEŁNIA ostatni przebieg i paliwo pojazdu z tabeli vehicles."""
        if index == -1:
            return

        conn = self.get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            vehicle_id = self.vehicle_combo.currentData()

            cursor.execute(
                """
                SELECT current_mileage, current_fuel, tank_capacity, registration_number
                FROM vehicles WHERE id=?
                """,
                (vehicle_id,),
            )

            row = cursor.fetchone()
            if row:
                last_mileage, last_fuel, tank_capacity, reg_number = row

                # Auto-wypełnianie przebiegu
                if self.checkout_mileage.value() == 0:
                    self.checkout_mileage.setValue(last_mileage or 0)

                # Auto-wypełnianie paliwa
                if self.checkout_fuel.value() == 0:
                    self.checkout_fuel.setValue(last_fuel if last_fuel is not None else 50.0)

                self.selected_vehicle_tank = tank_capacity or 100
                self.tank_info_label.setText(f"{self.selected_vehicle_tank:.1f} L (max)")

                tooltip = (
                    f"Auto-wypełniono:\n"
                    f"Przebieg: {float(last_mileage or 0):.1f} km\n"
                    f"Paliwo: {float(last_fuel or 0):.1f} L"
                )
                self.checkout_mileage.setToolTip(tooltip)
                self.checkout_fuel.setToolTip(tooltip)
                self.validate_fuel_tank()
        finally:
            conn.close()

    def validate_fuel_tank(self):
        """Walidacja: paliwo nie może przekroczyć pojemności baku."""
        fuel = self.checkout_fuel.value()
        tank = self.selected_vehicle_tank

        if tank and fuel > tank:
            self.checkout_fuel.setStyleSheet(
                "QDoubleSpinBox { background-color: #ff4444; color: white; }"
            )
            self.tank_info_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        else:
            self.checkout_fuel.setStyleSheet("")
            self.tank_info_label.setStyleSheet("QLabel { color: green; }")

    # ==========================
    # Baza danych + listy
    # ==========================

    def get_connection(self):
        try:
            return sqlite3.connect(self.db_path)
        except:
            return None

    def load_employees(self):
        conn = self.get_connection()
        if not conn:
            self.employee_count_label.setText("Pracownicy: BŁĄD BAZY")
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, first_name || ' ' || last_name, position
                FROM employees
                WHERE is_active = 1
                ORDER BY last_name, first_name
                """
            )

            rows = cursor.fetchall()
            self.employee_combo.clear()
            for emp_id, name, position in rows:
                self.employee_combo.addItem(f"{name} ({position})", emp_id)

            self.employee_count_label.setText(f"Pracownicy: {len(rows)}")
        finally:
            conn.close()

    def load_vehicles(self):
        conn = self.get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, registration_number, brand, model, current_fuel, tank_capacity
                FROM vehicles
                WHERE status = 'available'
                ORDER BY registration_number
                """
            )

            rows = cursor.fetchall()
            self.vehicle_combo.clear()
            for vid, reg, brand, model, fuel, tank in rows:
                fuel_text = f"{float(fuel or 0):.1f}L"
                self.vehicle_combo.addItem(
                    f"{reg} - {brand} {model} ({fuel_text})", vid
                )
        finally:
            conn.close()

    def refresh_lists(self):
        self.load_employees()
        self.load_vehicles()

    # ==========================
    # Walidacja
    # ==========================

    def validate_form(self) -> bool:
        errors = []

        if self.employee_combo.currentIndex() == -1:
            errors.append("Wybierz pracownika.")

        if self.vehicle_combo.currentIndex() == -1:
            errors.append("Wybierz pojazd.")

        if self.checkout_mileage.value() == 0:
            errors.append("Przebieg nie może być 0.")

        fuel = self.checkout_fuel.value()
        if self.selected_vehicle_tank and fuel > self.selected_vehicle_tank:
            errors.append(f"Paliwo > pojemność baku ({self.selected_vehicle_tank:.1f} L)!")

        if fuel < 0:
            errors.append("Paliwo nie może być ujemne.")

        if errors:
            QMessageBox.warning(self, "Błąd", "\n".join(errors))
            return False

        return True

    # ==========================
    # Wydanie klucza
    # ==========================

    def checkout_key(self):
        """WYDANIE KLUCZA Z BLOKADĄ DUPLIKATU I WALIDACJĄ PRZEBIEGU"""
        
        if not self.validate_form():
            return

        conn = self.get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            employee_id = self.employee_combo.currentData()
            vehicle_id = self.vehicle_combo.currentData()
            checkout_time = self.checkout_dt.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            checkout_mileage = self.checkout_mileage.value()
            checkout_fuel = self.checkout_fuel.value()
            storage_location = self.storage_location.text().strip()
            notes = self.notes.toPlainText().strip()

            # ✅ BLOKADA 1: Czy pojazd ma już AKTYWNY klucz (status='out')?
            cursor.execute(
                "SELECT COUNT(*) FROM key_log WHERE vehicle_id=? AND status='out'",
                (vehicle_id,),
            )
            active_keys = cursor.fetchone()[0]
            if active_keys > 0:
                QMessageBox.warning(
                    self,
                    "🚫 Pojazd już w użytkowaniu",
                    "Dla tego pojazdu jest już WYDANY kluczyk (status OUT).\n\n"
                    "Najpierw musisz ZWRÓCIĆ istniejący klucz,\n"
                    "dopiero potem możesz wydać nowy.\n\n"
                    f"🚗 Pojazd: {self.vehicle_combo.currentText()}",
                )
                return

            # ✅ BLOKADA 2: Czy nowy przebieg >= poprzedniemu?
            cursor.execute(
                "SELECT current_mileage FROM vehicles WHERE id=?",
                (vehicle_id,),
            )
            row = cursor.fetchone()
            current_vehicle_mileage = float(row[0] or 0) if row else 0.0

            if checkout_mileage < current_vehicle_mileage:
                QMessageBox.warning(
                    self,
                    "🚫 Błąd przebiegu",
                    f"Wpisany przebieg ({checkout_mileage:.1f} km) "
                    f"jest MNIEJSZY niż zapisany dla pojazdu ({current_vehicle_mileage:.1f} km).\n\n"
                    "⚠️ Licznik nie może się coofać!\n"
                    "Sprawdź odczyt na liczniku lub zmień wartość.",
                )
                return

            # ✅ Zapis rekordu w key_log
            cursor.execute(
                """
                INSERT INTO key_log (
                    vehicle_id, employee_id, checkout_time,
                    checkout_mileage, checkout_fuel,
                    storage_location, status, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, 'out', ?)
                """,
                (
                    vehicle_id,
                    employee_id,
                    checkout_time,
                    checkout_mileage,
                    checkout_fuel,
                    storage_location,
                    notes,
                ),
            )

            # ✅ Aktualizacja pojazdu
            cursor.execute(
                """
                UPDATE vehicles
                SET status='in_use', current_mileage=?, current_fuel=?
                WHERE id=?
                """,
                (checkout_mileage, checkout_fuel, vehicle_id),
            )

            conn.commit()

            QMessageBox.information(
                self,
                "✅ SUKCES - Kluczyk wydany",
                f"Pojazd: {self.vehicle_combo.currentText()}\n"
                f"Pracownik: {self.employee_combo.currentText()}\n\n"
                f"📏 Przebieg: {checkout_mileage:.1f} km\n"
                f"⛽ Stan paliwa: {checkout_fuel:.1f} L\n"
                f"🔑 Miejsce klucza: {storage_location or '(nie podano)'}\n\n"
                f"📍 Status pojazdu: IN_USE",
            )

            self.clear_form()
            self.load_vehicles()

        except Exception as e:
            QMessageBox.critical(self, "❌ Błąd bazy danych", str(e))
        finally:
            conn.close()

    def clear_form(self):
        self.employee_combo.setCurrentIndex(-1)
        self.vehicle_combo.setCurrentIndex(-1)
        self.checkout_dt.setDateTime(QDateTime.currentDateTime())
        self.checkout_mileage.setValue(0)
        self.checkout_fuel.setValue(0)
        self.storage_location.clear()
        self.notes.clear()
        self.tank_info_label.setText("Pojemność baku: -- L")
        self.selected_vehicle_tank = 0
        self.checkout_fuel.setStyleSheet("")
        self.tank_info_label.setStyleSheet("")

# ==========================
# Standalone test
# ==========================

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = KeyCheckoutWindow()
    window.setWindowTitle("Wydanie kluczyka")
    window.resize(950, 600)
    window.show()
    sys.exit(app.exec())