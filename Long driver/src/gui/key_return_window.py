# -*- coding: utf-8 -*-
"""
Okno zwrotu kluczyków - aktualizacja paliwa/przebiegu pojazdu
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

class KeyReturnWindow(QWidget):
    """Okno zwrotu kluczyków do pojazdu."""

    def __init__(self):
        super().__init__()
        self.db_path = Path(__file__).parent.parent.parent / "database" / "fleet.db"
        self.setup_ui()
        self.load_active_keylogs()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        header = QLabel("🔑 Zwrot kluczyka / zakończenie użycia pojazdu")
        font = QFont()
        font.setPointSize(16)
        font.setBold(True)
        header.setFont(font)
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        form_group = QGroupBox("Dane zwrotu")
        form_layout = QFormLayout()
        form_group.setLayout(form_layout)
        main_layout.addWidget(form_group)

        # Aktywne wydania kluczy (status='out')
        self.keylog_combo = QComboBox()
        self.keylog_combo.setPlaceholderText("Wybierz aktywne wydanie klucza")
        form_layout.addRow("Aktywne wypożyczenie:", self.keylog_combo)

        self.return_dt = QDateTimeEdit()
        self.return_dt.setCalendarPopup(True)
        self.return_dt.setDateTime(QDateTime.currentDateTime())
        form_layout.addRow("Data i godzina zwrotu:", self.return_dt)

        self.return_mileage = QDoubleSpinBox()
        self.return_mileage.setRange(0, 1_000_000)
        self.return_mileage.setDecimals(1)
        self.return_mileage.setSuffix(" km")
        form_layout.addRow("Przebieg przy zwrocie:", self.return_mileage)

        self.return_fuel = QDoubleSpinBox()
        self.return_fuel.setRange(0, 500)
        self.return_fuel.setDecimals(1)
        self.return_fuel.setSuffix(" L")
        form_layout.addRow("Paliwo przy zwrocie:", self.return_fuel)

        self.storage_location = QLineEdit()
        self.storage_location.setPlaceholderText("Np. Szafka A3, hak 5")
        form_layout.addRow("Miejsce klucza po zwrocie:", self.storage_location)

        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Uwagi o stanie pojazdu po zwrocie, szkody, paliwo itp.")
        form_layout.addRow("Uwagi:", self.notes)

        # Przyciski
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        self.return_button = QPushButton("✅ Zarejestruj zwrot klucza")
        self.return_button.clicked.connect(self.return_key)
        buttons_layout.addWidget(self.return_button)

        self.refresh_button = QPushButton("Odśwież listę")
        self.refresh_button.clicked.connect(self.load_active_keylogs)
        buttons_layout.addWidget(self.refresh_button)

        self.close_button = QPushButton("Zamknij")
        self.close_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.close_button)

        main_layout.addLayout(buttons_layout)

    def get_connection(self):
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd połączenia z bazą:\n{str(e)}")
            return None

    def load_active_keylogs(self):
        """Ładuje aktywne (niezwrócone) wydania kluczy."""
        conn = self.get_connection()
        if not conn:
            return
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT kl.id, v.registration_number, v.brand, v.model, 
                       e.first_name, e.last_name, kl.checkout_time, 
                       kl.checkout_mileage, kl.checkout_fuel
                FROM key_log kl
                JOIN vehicles v ON kl.vehicle_id = v.id
                JOIN employees e ON kl.employee_id = e.id
                WHERE kl.status = 'out'
                ORDER BY kl.checkout_time DESC
            """)
            rows = cursor.fetchall()
            self.keylog_combo.clear()
            for row in rows:
                log_id, reg, brand, model, first, last, checkout_time, checkout_mileage, checkout_fuel = row
                label = f"{log_id} | {reg} - {brand} {model} | {first} {last} | start: {checkout_time} | {checkout_mileage or 0:.1f}km, {checkout_fuel or 0:.1f}L"
                self.keylog_combo.addItem(label, log_id)
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd ładowania aktywnych wydań:\n{str(e)}")
        finally:
            conn.close()

    def validate_form(self) -> bool:
        errors = []
        if self.keylog_combo.currentIndex() == -1:
            errors.append("Wybierz aktywne wydanie klucza.")
        if self.return_mileage.value() == 0:
            errors.append("Podaj przebieg przy zwrocie.")
        if self.return_fuel.value() < 0:
            errors.append("Paliwo nie może być ujemne.")
        
        if errors:
            QMessageBox.warning(self, "Błąd walidacji", "\n".join(errors))
            return False
        return True

    def return_key(self):
        """Zamyka wpis w key_log i ustawia pojazd jako available."""
        if not self.validate_form():
            return

        conn = self.get_connection()
        if not conn:
            return

        try:
            cursor = conn.cursor()
            log_id = self.keylog_combo.currentData()
            return_time = self.return_dt.dateTime().toString("yyyy-MM-dd HH:mm:ss")
            return_mileage = self.return_mileage.value()
            return_fuel = self.return_fuel.value()
            storage_location = self.storage_location.text().strip()
            notes = self.notes.toPlainText().strip()

            # Pobierz vehicle_id z key_log
            cursor.execute("SELECT vehicle_id FROM key_log WHERE id = ?", (log_id,))
            row = cursor.fetchone()
            if not row:
                QMessageBox.critical(self, "Błąd", "Nie znaleziono wpisu w dzienniku kluczy.")
                return
            vehicle_id = row[0]

            # Zaktualizuj key_log (zwrot)
            cursor.execute("""
                UPDATE key_log 
                SET return_time = ?, return_mileage = ?, return_fuel = ?, 
                    storage_location = ?, status = 'returned',
                    notes = COALESCE(notes, ?) || CASE WHEN ? != '' THEN '\n' || ? ELSE '' END
                WHERE id = ?
            """, (return_time, return_mileage, return_fuel, storage_location, 
                  notes, notes, notes, log_id))

            # ZMIANA STATUSU: pojazd -> available + aktualizacja paliwo/przebieg
            cursor.execute("""
                UPDATE vehicles 
                SET status = 'available', current_mileage = ?, current_fuel = ?
                WHERE id = ?
            """, (return_mileage, return_fuel, vehicle_id))

            conn.commit()
            QMessageBox.information(
                self, "Sukces", 
                f"✅ Zwrot kluczyka zarejestrowany!\n"
                f"Pojazd: {vehicle_id}\n"
                f"Status zmieniony na: dostępny\n"
                f"Przebieg: {return_mileage:.1f} km\n"
                f"Paliwo: {return_fuel:.1f} L"
            )

            self.clear_form()
            self.load_active_keylogs()  # Odśwież listę

        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd rejestracji zwrotu:\n{str(e)}")
        finally:
            conn.close()

    def clear_form(self):
        """Czyści formularz zwrotu."""
        self.return_dt.setDateTime(QDateTime.currentDateTime())
        self.return_mileage.setValue(0)
        self.return_fuel.setValue(0)
        self.storage_location.clear()
        self.notes.clear()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    window = KeyReturnWindow()
    window.setWindowTitle("Test - Zwrot kluczyka")
    window.resize(900, 450)
    window.show()
    sys.exit(app.exec())
