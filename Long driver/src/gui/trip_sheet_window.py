# -*- coding: utf-8 -*-
"""
Moduł arkuszy przejazdów - widok i (w przyszłości) generowanie PDF
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QComboBox, QDateEdit, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont
import sqlite3
from pathlib import Path


class TripSheetWindow(QWidget):
    """Okno arkuszy przejazdów (karta drogowa)"""

    def __init__(self):
        super().__init__()
        self.db_path = Path(__file__).parent.parent.parent / "database" / "fleet.db"
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        """Konfiguruje interfejs"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Nagłówek
        header = QLabel("📝 Arkusze Przejazdów (karta drogowa)")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Filtry
        filter_layout = QHBoxLayout()

        self.vehicle_filter = QComboBox()
        self.vehicle_filter.setPlaceholderText("Wszystkie pojazdy")
        self.vehicle_filter.setFixedWidth(250)
        self.vehicle_filter.currentTextChanged.connect(self.load_data)

        self.date_filter = QDateEdit()
        self.date_filter.setCalendarPopup(True)
        self.date_filter.setDate(QDate.currentDate())
        self.date_filter.setFixedWidth(150)
        self.date_filter.dateChanged.connect(self.load_data)

        self.generate_button = QPushButton("📄 Generuj PDF")
        self.generate_button.setStyleSheet("background-color: #16a085; color: white; font-weight: bold;")
        self.generate_button.clicked.connect(self.generate_pdf_report)

        filter_layout.addWidget(QLabel("Pojazd:"))
        filter_layout.addWidget(self.vehicle_filter)
        filter_layout.addWidget(QLabel("Miesiąc:"))
        filter_layout.addWidget(self.date_filter)
        filter_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
        filter_layout.addWidget(self.generate_button)

        main_layout.addLayout(filter_layout)

        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "ID", "Nr rej.", "Kierowca", "Data", "Cel",
            "Przebieg start", "Przebieg koniec", "Dystans",
            "Paliwo zużyte", "Śr. spalanie", "Uwagi"
        ])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(10, QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        main_layout.addWidget(self.table)

    # ==========================
    # Baza danych
    # ==========================
    def get_connection(self):
        """Połączenie z bazą"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd połączenia:\n{str(e)}")
            return None

    def load_data(self):
        """Ładuje dane do tabeli"""
        conn = self.get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()

            # Załaduj pojazdy do filtra (tylko raz)
            if self.vehicle_filter.count() == 0:
                cursor.execute("""
                    SELECT id, registration_number, brand, model
                    FROM vehicles
                    ORDER BY registration_number
                """)
                vehicles = cursor.fetchall()
                self.vehicle_filter.addItem("Wszystkie pojazdy", -1)
                for vid, reg, brand, model in vehicles:
                    self.vehicle_filter.addItem(f"{reg} - {brand} {model}", vid)

            # Buduj zapytanie SQL
            query = """
                SELECT
                    t.id,
                    v.registration_number,
                    e.first_name || ' ' || e.last_name,
                    strftime('%d.%m.%Y', t.start_date),
                    t.purpose,
                    t.start_mileage,
                    t.end_mileage,
                    t.distance,
                    t.fuel_used,
                    CASE
                        WHEN t.distance > 0 AND t.fuel_used > 0
                        THEN (t.fuel_used / t.distance) * 100
                        ELSE NULL
                    END as avg_consumption,
                    t.notes
                FROM trips t
                JOIN vehicles v ON t.vehicle_id = v.id
                JOIN employees e ON t.employee_id = e.id
                WHERE strftime('%Y-%m', t.start_date) = ?
            """
            params = [self.date_filter.date().toString("yyyy-MM")]

            if self.vehicle_filter.currentIndex() > 0:
                query += " AND t.vehicle_id = ?"
                params.append(self.vehicle_filter.currentData())

            query += " ORDER BY t.start_date"

            cursor.execute(query, params)
            trips = cursor.fetchall()

            self.table.setRowCount(len(trips))
            for row_idx, trip in enumerate(trips):
                for col_idx, value in enumerate(trip):
                    item = QTableWidgetItem(str(value) if value is not None else "")

                    # Formatowanie liczb
                    if col_idx in [5, 6, 7] and value is not None:
                        try:
                            item.setText(f"{float(value):.1f} km")
                        except Exception:
                            pass
                    elif col_idx == 8 and value is not None:
                        try:
                            item.setText(f"{float(value):.2f} L")
                        except Exception:
                            pass
                    elif col_idx == 9 and value is not None:
                        try:
                            item.setText(f"{float(value):.2f} L/100km")
                        except Exception:
                            pass

                    self.table.setItem(row_idx, col_idx, item)

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd ładowania danych:\n{str(e)}")
        finally:
            conn.close()

    def generate_pdf_report(self):
        """Generuje raport PDF (placeholder)"""
        QMessageBox.information(
            self,
            "Informacja",
            "Funkcja generowania raportów PDF jest w trakcie przygotowania.\n"
            "Dane karty drogowej widzisz w tabeli powyżej."
        )


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    window = TripSheetWindow()
    window.setWindowTitle("Test - Arkusze Przejazdów")
    window.resize(1200, 700)
    window.show()
    sys.exit(app.exec())
