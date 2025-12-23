# -*- coding: utf-8 -*-
"""
Okno pojazdów – dane pojazdu na scrollu + pasek paliwa z edytowalnym poziomem.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QTextEdit, QComboBox, QFormLayout, QGroupBox,
    QDoubleSpinBox, QSpinBox, QProgressBar, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import sqlite3
from pathlib import Path


class FuelProgressBar(QProgressBar):
    """Pasek paliwa z kolorami (zielony→żółty→czerwony)."""

    def __init__(self):
        super().__init__()
        self.setRange(0, 100)
        self.setTextVisible(True)
        self.setFixedHeight(25)
        self.update_style(100)

    def update_style(self, fuel_percent: float):
        """Zmienia kolor w zależności od poziomu paliwa."""
        if fuel_percent >= 70:
            color = "#27ae60"  # zielony
        elif fuel_percent >= 40:
            color = "#f39c12"  # pomarańczowy
        elif fuel_percent >= 20:
            color = "#f1c40f"  # żółty
        else:
            color = "#e74c3c"  # czerwony

        style = f"""
        QProgressBar {{
            border: 2px solid gray;
            border-radius: 5px;
            text-align: center;
            background-color: #2c3e50;
            color: white;
            font-weight: bold;
        }}
        QProgressBar::chunk {{
            background-color: {color};
            border-radius: 3px;
        }}
        """
        self.setStyleSheet(style)

    def set_fuel_level(self, fuel: float, tank_capacity: float):
        """Ustawia pasek paliwa na podstawie litrów i pojemności baku."""
        if tank_capacity > 0:
            percent = min(100, max(0, (fuel / tank_capacity) * 100))
            self.setValue(int(percent))
            self.update_style(percent)
            self.setFormat(f"{fuel:.1f} L ({percent:.0f}%)")
        else:
            self.setValue(0)
            self.setFormat(f"{fuel:.1f} L (brak baku)")


class VehicleWindow(QWidget):
    """Okno zarządzania pojazdami."""

    def __init__(self):
        super().__init__()
        self.db_path = Path(__file__).parent.parent.parent / "database" / "fleet.db"
        self.setup_ui()
        self.load_vehicles()
        self.resize(1400, 750)

    # ==========================
    # UI
    # ==========================
    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        header = QLabel("🚗 Zarządzanie Pojazdami")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # --- Formularz (w środku scrolla) ---
        form_group = QGroupBox("Dane pojazdu")
        form_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)

        self.vehicle_id = QLineEdit()
        self.vehicle_id.setVisible(False)

        self.reg_number = QLineEdit()
        self.reg_number.setPlaceholderText("np. WX 12345")

        self.brand = QLineEdit()
        self.brand.setPlaceholderText("np. Ford")

        self.model = QLineEdit()
        self.model.setPlaceholderText("np. Transit")

        self.fuel_type = QComboBox()
        self.fuel_type.addItems(["Benzyna", "Diesel", "LPG", "Hybryda", "Elektryk"])

        self.fuel_consumption = QDoubleSpinBox()
        self.fuel_consumption.setRange(0, 30)
        self.fuel_consumption.setDecimals(1)
        self.fuel_consumption.setValue(7.5)
        self.fuel_consumption.setSuffix(" L/100km")

        self.current_mileage = QDoubleSpinBox()
        self.current_mileage.setRange(0, 1_000_000)
        self.current_mileage.setDecimals(1)
        self.current_mileage.setValue(10_000)
        self.current_mileage.setSuffix(" km")

        # --- Poziom paliwa: pole + pasek ---
        self.current_fuel = QDoubleSpinBox()
        self.current_fuel.setRange(0, 200)
        self.current_fuel.setDecimals(1)
        self.current_fuel.setValue(50.0)
        self.current_fuel.setSuffix(" L")
        self.current_fuel.setMinimumWidth(80)
        self.current_fuel.setFixedHeight(26)
        self.current_fuel.setStyleSheet(
            "QDoubleSpinBox { background-color: #2b2b2b; color: white; padding: 2px; }"
        )
        self.current_fuel.valueChanged.connect(self.update_fuel_bar)

        self.fuel_bar = FuelProgressBar()

        fuel_layout = QHBoxLayout()
        fuel_layout.addWidget(self.current_fuel, 0)   # nie rozciąga się
        fuel_layout.addWidget(self.fuel_bar, 1)       # pasek rośnie

        fuel_widget = QWidget()
        fuel_widget.setLayout(fuel_layout)

        self.tank_capacity = QDoubleSpinBox()
        self.tank_capacity.setRange(0, 300)
        self.tank_capacity.setDecimals(1)
        self.tank_capacity.setSuffix(" L")
        self.tank_capacity.valueChanged.connect(self.update_fuel_bar)

        self.vin = QLineEdit()
        self.vin.setPlaceholderText("VIN (opcjonalnie)")

        self.production_year = QSpinBox()
        self.production_year.setRange(1970, 2100)
        self.production_year.setValue(2020)

        self.status = QComboBox()
        self.status.addItems(["available", "in_use", "service", "broken"])

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Uwagi o pojeździe...")

        form_layout.addRow("ID:", self.vehicle_id)
        form_layout.addRow("Nr rejestracyjny*:", self.reg_number)
        form_layout.addRow("Marka*:", self.brand)
        form_layout.addRow("Model*:", self.model)
        form_layout.addRow("Rodzaj paliwa:", self.fuel_type)
        form_layout.addRow("Średnie spalanie:", self.fuel_consumption)
        form_layout.addRow("Przebieg aktualny:", self.current_mileage)
        form_layout.addRow("Poziom paliwa:", fuel_widget)
        form_layout.addRow("Pojemność baku:", self.tank_capacity)
        form_layout.addRow("Rok produkcji:", self.production_year)
        form_layout.addRow("VIN:", self.vin)
        form_layout.addRow("Status:", self.status)
        form_layout.addRow("Uwagi:", self.notes)

        # --- Przyciski formularza ---
        buttons_layout = QHBoxLayout()

        self.add_button = QPushButton("➕ Dodaj pojazd")
        self.add_button.setStyleSheet(
            "background-color: #27ae60; color: white; font-weight: bold;"
        )
        self.add_button.clicked.connect(self.add_vehicle)

        self.update_button = QPushButton("✏️ Aktualizuj")
        self.update_button.setStyleSheet(
            "background-color: #3498db; color: white; font-weight: bold;"
        )
        self.update_button.clicked.connect(self.update_vehicle)
        self.update_button.setEnabled(False)

        self.delete_button = QPushButton("🗑️ Usuń")
        self.delete_button.setStyleSheet("background-color: #c0392b; color: white;")
        self.delete_button.clicked.connect(self.delete_selected)

        self.clear_button = QPushButton("Wyczyść")
        self.clear_button.setStyleSheet("background-color: #95a5a6; color: white;")
        self.clear_button.clicked.connect(self.clear_form)

        buttons_layout.addWidget(self.add_button)
        buttons_layout.addWidget(self.update_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.clear_button)

        form_layout.addRow(buttons_layout)

        # --- Scroll dla formularza ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(form_group)

        # --- Tabela ---
        table_group = QGroupBox("Lista pojazdów")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nr rej.", "Marka", "Model", "Paliwo", "Spalanie",
            "Przebieg", "Stan paliwa", "Status", "Bak", "Uwagi"
        ])

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.Stretch)

        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.load_vehicle_to_form)

        table_layout.addWidget(self.table)

        # --- Do głównego layoutu ---
        content_layout.addWidget(scroll, 1)      # formularz ze scrollem
        content_layout.addWidget(table_group, 2) # tabela

    # ==========================
    # Logika paliwa
    # ==========================
    def update_fuel_bar(self):
        """Aktualizuje pasek paliwa."""
        fuel = self.current_fuel.value()
        tank = self.tank_capacity.value()
        self.fuel_bar.set_fuel_level(fuel, tank)

    # ==========================
    # Baza danych
    # ==========================
    def get_connection(self):
        try:
            return sqlite3.connect(self.db_path)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd połączenia:\n{str(e)}")
            return None

    def load_vehicles(self):
        conn = self.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, registration_number, brand, model, fuel_type,
                       fuel_consumption, current_mileage, current_fuel, status,
                       tank_capacity, notes
                FROM vehicles
                ORDER BY registration_number
            """)
            rows = cursor.fetchall()
            self.table.setRowCount(len(rows))

            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    if col_idx in (5, 6, 7, 9):  # spalanie, przebieg, paliwo, bak
                        try:
                            num = float(value or 0)
                            if col_idx == 5:
                                text = f"{num:.1f} L/100km"
                            elif col_idx == 6:
                                text = f"{num:.1f} km"
                            else:
                                text = f"{num:.1f} L"
                            item = QTableWidgetItem(text)
                        except Exception:
                            item = QTableWidgetItem(str(value))
                    else:
                        item = QTableWidgetItem(str(value) if value is not None else "")

                    # status – kolor tła
                    if col_idx == 8:
                        status = str(value)
                        colors = {
                            "available": QColor(144, 238, 144, 100),
                            "in_use": QColor(255, 255, 0, 100),
                            "service": QColor(135, 206, 250, 100),
                            "broken": QColor(255, 99, 71, 100),
                        }
                        if status in colors:
                            item.setBackground(colors[status])

                    # Stan paliwa – kolor w zależności od % baku
                    if col_idx == 7 and row[9]:
                        try:
                            fuel_percent = min(
                                100,
                                max(0, (float(value or 0) / float(row[9])) * 100)
                            )
                            item.setBackground(QColor(
                                max(0, 255 - int(fuel_percent * 2.55)),
                                int(fuel_percent * 2.55),
                                0,
                                100
                            ))
                        except Exception:
                            pass

                    self.table.setItem(row_idx, col_idx, item)
        finally:
            conn.close()

    # ==========================
    # Operacje na pojazdach
    # ==========================
    def add_vehicle(self):
        if not self.validate_form():
            return
        conn = self.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vehicles (
                    registration_number, brand, model, fuel_type,
                    fuel_consumption, current_mileage, current_fuel, status,
                    tank_capacity, vin, production_year, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.reg_number.text().strip().upper(),
                self.brand.text().strip(),
                self.model.text().strip(),
                self.fuel_type.currentText(),
                self.fuel_consumption.value(),
                self.current_mileage.value(),
                self.current_fuel.value(),
                self.status.currentText(),
                self.tank_capacity.value() if self.tank_capacity.value() > 0 else None,
                self.vin.text().strip() or None,
                self.production_year.value(),
                self.notes.toPlainText().strip()
            ))
            conn.commit()
            QMessageBox.information(self, "Sukces", "🚗 Pojazd dodany!")
            self.load_vehicles()
            self.clear_form()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Błąd", "Nr rejestracyjny już istnieje!")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))
        finally:
            conn.close()

    def update_vehicle(self):
        if not self.vehicle_id.text():
            QMessageBox.warning(self, "Błąd", "Wybierz pojazd do edycji!")
            return
        if not self.validate_form():
            return
        conn = self.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE vehicles
                SET registration_number=?, brand=?, model=?, fuel_type=?,
                    fuel_consumption=?, current_mileage=?, current_fuel=?, status=?,
                    tank_capacity=?, vin=?, production_year=?, notes=?
                WHERE id=?
            """, (
                self.reg_number.text().strip().upper(),
                self.brand.text().strip(),
                self.model.text().strip(),
                self.fuel_type.currentText(),
                self.fuel_consumption.value(),
                self.current_mileage.value(),
                self.current_fuel.value(),
                self.status.currentText(),
                self.tank_capacity.value() if self.tank_capacity.value() > 0 else None,
                self.vin.text().strip() or None,
                self.production_year.value(),
                self.notes.toPlainText().strip(),
                int(self.vehicle_id.text())
            ))
            conn.commit()
            QMessageBox.information(self, "Sukces", "🚗 Pojazd zaktualizowany!")
            self.load_vehicles()
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", str(e))
        finally:
            conn.close()

    def delete_selected(self):
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Błąd", "Wybierz pojazdy!")
            return

        reply = QMessageBox.question(
            self, "Potwierdź",
            f"Usunąć {len(selected_rows)} pojazdów?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        conn = self.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            for row in selected_rows:
                vehicle_id = int(self.table.item(row, 0).text())
                cursor.execute("DELETE FROM vehicles WHERE id=?", (vehicle_id,))
            conn.commit()
            QMessageBox.information(self, "Sukces", f"🗑️ Usunięto {len(selected_rows)} pojazdów!")
            self.load_vehicles()
        finally:
            conn.close()

    def load_vehicle_to_form(self, index):
        row = index.row()
        self.vehicle_id.setText(self.table.item(row, 0).text())
        self.reg_number.setText(self.table.item(row, 1).text())
        self.brand.setText(self.table.item(row, 2).text())
        self.model.setText(self.table.item(row, 3).text())

        fuel_type = self.table.item(row, 4).text()
        idx = self.fuel_type.findText(fuel_type)
        if idx >= 0:
            self.fuel_type.setCurrentIndex(idx)

        try:
            self.fuel_consumption.setValue(
                float(self.table.item(row, 5).text().split()[0])
            )
        except Exception:
            pass

        try:
            self.current_mileage.setValue(
                float(self.table.item(row, 6).text().split()[0])
            )
        except Exception:
            pass

        try:
            fuel_text = self.table.item(row, 7).text().split()[0]
            self.current_fuel.setValue(float(fuel_text))
        except Exception:
            pass

        status_text = self.table.item(row, 8).text()
        idx = self.status.findText(status_text)
        if idx >= 0:
            self.status.setCurrentIndex(idx)

        try:
            self.tank_capacity.setValue(
                float(self.table.item(row, 9).text().split()[0])
            )
        except Exception:
            pass

        self.notes.setText(self.table.item(row, 10).text())
        self.update_fuel_bar()
        self.add_button.setEnabled(False)
        self.update_button.setEnabled(True)

    def clear_form(self):
        self.vehicle_id.clear()
        self.reg_number.clear()
        self.brand.clear()
        self.model.clear()
        self.fuel_type.setCurrentIndex(0)
        self.fuel_consumption.setValue(7.5)
        self.current_mileage.setValue(10_000)
        self.current_fuel.setValue(50.0)
        self.tank_capacity.setValue(60)
        self.vin.clear()
        self.production_year.setValue(2020)
        self.status.setCurrentIndex(0)
        self.notes.clear()
        self.fuel_bar.set_fuel_level(50, 60)
        self.add_button.setEnabled(True)
        self.update_button.setEnabled(False)

    def validate_form(self) -> bool:
        errors = []
        if not self.reg_number.text().strip():
            errors.append("Nr rejestracyjny wymagany")
        if not self.brand.text().strip():
            errors.append("Marka wymagana")
        if not self.model.text().strip():
            errors.append("Model wymagany")
        if self.current_fuel.value() > self.tank_capacity.value():
            errors.append("Stan paliwa > Pojemność baku!")

        if errors:
            QMessageBox.warning(self, "Błąd walidacji", "\n".join(errors))
            return False
        return True


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = VehicleWindow()
    window.setWindowTitle("Zarządzanie Pojazdami")
    window.show()
    sys.exit(app.exec())
