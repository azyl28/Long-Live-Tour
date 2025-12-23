# -*- coding: utf-8 -*-
"""
Okno zarządzania pojazdami
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QTextEdit, QComboBox, QFormLayout, QGroupBox,
    QDoubleSpinBox, QSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor

import sqlite3
from pathlib import Path


class VehicleWindow(QWidget):
    """Okno zarządzania pojazdami"""

    def __init__(self):
        super().__init__()
        self.db_path = Path(__file__).parent.parent.parent / "database" / "fleet.db"
        self.setup_ui()
        self.load_vehicles()

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

        # Formularz
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

        self.tank_capacity = QDoubleSpinBox()
        self.tank_capacity.setRange(0, 300)
        self.tank_capacity.setDecimals(1)
        self.tank_capacity.setSuffix(" L")

        self.vin = QLineEdit()
        self.vin.setPlaceholderText("VIN (opcjonalnie)")

        self.production_year = QSpinBox()
        self.production_year.setRange(1970, 2100)
        self.production_year.setValue(2020)

        # Statusy zgodne ze schematem bazy
        self.status = QComboBox()
        self.status.addItems([
            "available",   # dostępny
            "in_use",      # w trasie
            "service",     # w serwisie
            "broken"       # niesprawny
        ])

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Uwagi o pojeździe...")

        form_layout.addRow("ID:", self.vehicle_id)
        form_layout.addRow("Nr rejestracyjny*:", self.reg_number)
        form_layout.addRow("Marka*:", self.brand)
        form_layout.addRow("Model*:", self.model)
        form_layout.addRow("Rodzaj paliwa:", self.fuel_type)
        form_layout.addRow("Średnie spalanie:", self.fuel_consumption)
        form_layout.addRow("Przebieg aktualny:", self.current_mileage)
        form_layout.addRow("Pojemność baku:", self.tank_capacity)
        form_layout.addRow("Rok produkcji:", self.production_year)
        form_layout.addRow("VIN:", self.vin)
        form_layout.addRow("Status:", self.status)
        form_layout.addRow("Uwagi:", self.notes)

        # Przyciski formularza
        buttons_layout = QHBoxLayout()
        self.add_button = QPushButton("➕ Dodaj pojazd")
        self.add_button.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.add_button.clicked.connect(self.add_vehicle)

        self.update_button = QPushButton("✏️ Aktualizuj")
        self.update_button.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
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

        # Tabela
        table_group = QGroupBox("Lista pojazdów")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nr rej.", "Marka", "Model", "Paliwo",
            "Spalanie", "Przebieg", "Status", "Bak", "Uwagi"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(9, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.load_vehicle_to_form)

        table_layout.addWidget(self.table)

        # Dodaj do layoutu głównego
        content_layout.addWidget(form_group, 1)
        content_layout.addWidget(table_group, 2)

    # ==========================
    # Baza danych
    # ==========================
    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd połączenia z bazą:\n{str(e)}")
            return None

    def load_vehicles(self):
        """Ładuje listę pojazdów do tabeli."""
        conn = self.get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    id,
                    registration_number,
                    brand,
                    model,
                    fuel_type,
                    fuel_consumption,
                    current_mileage,
                    status,
                    tank_capacity,
                    notes
                FROM vehicles
                ORDER BY registration_number
            """)
            rows = cursor.fetchall()

            self.table.setRowCount(len(rows))
            for row_idx, row in enumerate(rows):
                for col_idx, value in enumerate(row):
                    if col_idx in (5, 6, 8) and value is not None:
                        # Spalanie / przebieg / bak - formatowanie liczb
                        try:
                            num = float(value)
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

                    # Kolorowanie statusu
                    if col_idx == 7:
                        status = str(value)
                        if status == "available":
                            item.setBackground(QColor(144, 238, 144, 100))  # zielony
                        elif status == "in_use":
                            item.setBackground(QColor(255, 255, 0, 100))    # żółty
                        elif status == "service":
                            item.setBackground(QColor(135, 206, 250, 100))  # niebieski
                        elif status == "broken":
                            item.setBackground(QColor(255, 99, 71, 100))    # czerwony

                    self.table.setItem(row_idx, col_idx, item)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd ładowania pojazdów:\n{str(e)}")
        finally:
            conn.close()

    # ==========================
    # Operacje na pojazdach
    # ==========================
    def add_vehicle(self):
        """Dodaje nowy pojazd"""
        if not self.validate_form():
            return

        conn = self.get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO vehicles
                (registration_number, brand, model, fuel_type,
                 fuel_consumption, current_mileage, status,
                 tank_capacity, vin, production_year, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.reg_number.text().strip().upper(),
                self.brand.text().strip(),
                self.model.text().strip(),
                self.fuel_type.currentText(),
                self.fuel_consumption.value(),
                self.current_mileage.value(),
                self.status.currentText(),
                self.tank_capacity.value() if self.tank_capacity.value() > 0 else None,
                self.vin.text().strip() or None,
                self.production_year.value(),
                self.notes.toPlainText().strip()
            ))
            conn.commit()
            QMessageBox.information(self, "Sukces", "Pojazd został dodany!")

            self.load_vehicles()
            self.clear_form()

        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Błąd", "Pojazd o tym numerze rejestracyjnym już istnieje!")
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd dodawania pojazdu:\n{str(e)}")
        finally:
            conn.close()

    def update_vehicle(self):
        """Aktualizuje istniejący pojazd"""
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
                SET registration_number = ?, brand = ?, model = ?, fuel_type = ?,
                    fuel_consumption = ?, current_mileage = ?, status = ?,
                    tank_capacity = ?, vin = ?, production_year = ?, notes = ?
                WHERE id = ?
            """, (
                self.reg_number.text().strip().upper(),
                self.brand.text().strip(),
                self.model.text().strip(),
                self.fuel_type.currentText(),
                self.fuel_consumption.value(),
                self.current_mileage.value(),
                self.status.currentText(),
                self.tank_capacity.value() if self.tank_capacity.value() > 0 else None,
                self.vin.text().strip() or None,
                self.production_year.value(),
                self.notes.toPlainText().strip(),
                int(self.vehicle_id.text())
            ))
            conn.commit()
            QMessageBox.information(self, "Sukces", "Pojazd został zaktualizowany!")

            self.load_vehicles()
            self.clear_form()

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd aktualizacji:\n{str(e)}")
        finally:
            conn.close()

    def delete_selected(self):
        """Usuwa zaznaczone pojazdy"""
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Błąd", "Wybierz pojazdy do usunięcia!")
            return

        reply = QMessageBox.question(
            self, "Potwierdzenie",
            f"Czy na pewno chcesz usunąć {len(selected_rows)} pojazd(ów)?",
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
                cursor.execute("DELETE FROM vehicles WHERE id = ?", (vehicle_id,))
            conn.commit()
            QMessageBox.information(self, "Sukces", "Pojazdy zostały usunięte!")

            self.load_vehicles()

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd usuwania:\n{str(e)}")
        finally:
            conn.close()

    def load_vehicle_to_form(self, index):
        """Ładuje dane pojazdu do formularza po dwukliku"""
        row = index.row()

        self.vehicle_id.setText(self.table.item(row, 0).text())
        self.reg_number.setText(self.table.item(row, 1).text())
        self.brand.setText(self.table.item(row, 2).text())
        self.model.setText(self.table.item(row, 3).text())

        fuel_type = self.table.item(row, 4).text()
        idx = self.fuel_type.findText(fuel_type)
        if idx >= 0:
            self.fuel_type.setCurrentIndex(idx)

        # Spalanie (bez jednostki)
        try:
            fc_text = self.table.item(row, 5).text().split()[0]
            self.fuel_consumption.setValue(float(fc_text))
        except Exception:
            pass

        # Przebieg
        try:
            mileage_text = self.table.item(row, 6).text().split()[0]
            self.current_mileage.setValue(float(mileage_text))
        except Exception:
            pass

        status_text = self.table.item(row, 7).text()
        idx = self.status.findText(status_text)
        if idx >= 0:
            self.status.setCurrentIndex(idx)

        # Bak
        try:
            tank_text = self.table.item(row, 8).text().split()[0]
            self.tank_capacity.setValue(float(tank_text))
        except Exception:
            pass

        self.notes.setText(self.table.item(row, 9).text())

        self.add_button.setEnabled(False)
        self.update_button.setEnabled(True)

    def clear_form(self):
        """Czyści formularz"""
        self.vehicle_id.clear()
        self.reg_number.clear()
        self.brand.clear()
        self.model.clear()
        self.fuel_type.setCurrentIndex(0)
        self.fuel_consumption.setValue(7.5)
        self.current_mileage.setValue(10_000)
        self.tank_capacity.setValue(0)
        self.vin.clear()
        self.production_year.setValue(2020)
        self.status.setCurrentIndex(0)
        self.notes.clear()
        self.add_button.setEnabled(True)
        self.update_button.setEnabled(False)

    def validate_form(self) -> bool:
        """Waliduje dane w formularzu"""
        errors = []
        if not self.reg_number.text().strip():
            errors.append("Numer rejestracyjny jest wymagany")
        if not self.brand.text().strip():
            errors.append("Marka jest wymagana")
        if not self.model.text().strip():
            errors.append("Model jest wymagany")

        if errors:
            QMessageBox.warning(self, "Błąd walidacji", "\n".join(errors))
            return False
        return True


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = VehicleWindow()
    window.setWindowTitle("Test - Zarządzanie Pojazdami")
    window.resize(1200, 600)
    window.show()
    sys.exit(app.exec())
