"""
Okno zarządzania pracownikami
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QLineEdit, QComboBox, QFormLayout, QGroupBox, QCheckBox,
    QTextEdit, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QColor
import sqlite3
from pathlib import Path

class EmployeeWindow(QWidget):
    """Okno zarządzania pracownikami"""
    
    def __init__(self):
        super().__init__()
        self.db_path = Path(__file__).parent.parent.parent / "database" / "fleet.db"
        self.setup_ui()
        self.load_employees()
    
    def setup_ui(self):
        """Konfiguruje interfejs"""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Nagłówek
        header = QLabel("👥 Zarządzanie Pracownikami")
        header_font = QFont()
        header_font.setPointSize(16)
        header_font.setBold(True)
        header.setFont(header_font)
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Formularz
        form_widget = QWidget()
        form_layout = QVBoxLayout()
        
        form_group = QGroupBox("Dodaj/Edytuj pracownika")
        form_group.setStyleSheet("QGroupBox { font-weight: bold; }")
        
        form = QFormLayout()
        
        self.employee_id = QLineEdit()
        self.employee_id.setVisible(False)
        
        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("np. Jan")
        
        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("np. Kowalski")
        
        self.position = QLineEdit()
        self.position.setPlaceholderText("np. Kierowca")
        
        self.department = QComboBox()
        self.department.addItems(["Kierowcy", "Administracja", "Serwis", "Kadry", "Finanse", "IT"])
        self.department.setEditable(True)
        
        self.permissions = QComboBox()
        self.permissions.addItems(["pracownik", "kierownik", "administrator"])
        
        self.email = QLineEdit()
        self.email.setPlaceholderText("np. jan.kowalski@firma.pl")
        
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("np. 123-456-789")
        
        self.is_active = QCheckBox("Aktywny")
        self.is_active.setChecked(True)
        
        self.notes = QTextEdit()
        self.notes.setMaximumHeight(80)
        self.notes.setPlaceholderText("Dodatkowe uwagi...")
        
        form.addRow("ID:", self.employee_id)
        form.addRow("Imię*:", self.first_name)
        form.addRow("Nazwisko*:", self.last_name)
        form.addRow("Stanowisko*:", self.position)
        form.addRow("Dział:", self.department)
        form.addRow("Uprawnienia:", self.permissions)
        form.addRow("Email:", self.email)
        form.addRow("Telefon:", self.phone)
        form.addRow("Status:", self.is_active)
        form.addRow("Uwagi:", self.notes)
        
        form_group.setLayout(form)
        form_layout.addWidget(form_group)
        
        # Przyciski formularza
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("➕ Dodaj")
        self.add_button.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold;")
        self.add_button.clicked.connect(self.add_employee)
        
        self.update_button = QPushButton("✏️ Aktualizuj")
        self.update_button.setStyleSheet("background-color: #3498db; color: white; font-weight: bold;")
        self.update_button.clicked.connect(self.update_employee)
        self.update_button.setEnabled(False)
        
        self.clear_button = QPushButton("🗑️ Wyczyść")
        self.clear_button.setStyleSheet("background-color: #95a5a6; color: white;")
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.clear_button)
        
        form_layout.addLayout(button_layout)
        form_widget.setLayout(form_layout)
        
        # Tabela
        table_widget = QWidget()
        table_layout = QVBoxLayout()
        
        # Przyciski nad tabelą
        top_buttons = QHBoxLayout()
        
        self.refresh_button = QPushButton("🔄 Odśwież")
        self.refresh_button.clicked.connect(self.load_employees)
        
        self.delete_button = QPushButton("🗑️ Usuń zaznaczone")
        self.delete_button.setStyleSheet("background-color: #e74c3c; color: white;")
        self.delete_button.clicked.connect(self.delete_selected)
        
        top_buttons.addWidget(self.refresh_button)
        top_buttons.addWidget(self.delete_button)
        top_buttons.addStretch()
        
        table_layout.addLayout(top_buttons)
        
        # Tabela pracowników
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "ID", "Imię", "Nazwisko", "Stanowisko", 
            "Dział", "Uprawnienia", "Email", "Telefon", "Status"
        ])
        
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Nazwisko rozciągliwe
        
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.load_employee_to_form)
        
        table_layout.addWidget(self.table)
        table_widget.setLayout(table_layout)
        
        # Dodaj do splittera
        splitter.addWidget(form_widget)
        splitter.addWidget(table_widget)
        splitter.setSizes([400, 800])
        
        main_layout.addWidget(splitter)
        
        # Statystyki
        stats_layout = QHBoxLayout()
        
        self.total_label = QLabel("Łącznie: 0 pracowników")
        self.active_label = QLabel("Aktywni: 0")
        self.drivers_label = QLabel("Kierowcy: 0")
        
        stats_layout.addWidget(self.total_label)
        stats_layout.addWidget(self.active_label)
        stats_layout.addWidget(self.drivers_label)
        stats_layout.addStretch()
        
        main_layout.addLayout(stats_layout)
    
    def get_connection(self):
        """Połączenie z bazą danych"""
        try:
            conn = sqlite3.connect(self.db_path)
            return conn
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie można połączyć z bazą:\n{str(e)}")
            return None
    
    def load_employees(self):
        """Ładuje pracowników do tabeli"""
        conn = self.get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, first_name, last_name, position, 
                       department, permissions, email, phone, is_active
                FROM employees
                ORDER BY last_name, first_name
            """)
            
            employees = cursor.fetchall()
            self.table.setRowCount(len(employees))
            
            for row_idx, emp in enumerate(employees):
                for col_idx, value in enumerate(emp):
                    item = QTableWidgetItem(str(value))
                    
                    # Kolorowanie statusu
                    if col_idx == 8:  # Kolumna is_active
                        if value == 1 or value == '1' or value is True:
                            item.setBackground(QColor(144, 238, 144))  # zielony
                            item.setText("Aktywny")
                        else:
                            item.setBackground(QColor(255, 99, 71))    # czerwony
                            item.setText("Nieaktywny")
                    
                    self.table.setItem(row_idx, col_idx, item)
            
            self.update_statistics(cursor)
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd ładowania:\n{str(e)}")
        finally:
            conn.close()
    
    def update_statistics(self, cursor):
        """Aktualizuje statystyki"""
        try:
            # Łączna liczba
            cursor.execute("SELECT COUNT(*) FROM employees")
            total = cursor.fetchone()[0]
            
            # Aktywni
            cursor.execute("SELECT COUNT(*) FROM employees WHERE is_active = 1")
            active = cursor.fetchone()[0]
            
            # Kierowcy
            cursor.execute("SELECT COUNT(*) FROM employees WHERE position LIKE '%kierowca%' OR position LIKE '%driver%'")
            drivers = cursor.fetchone()[0]
            
            self.total_label.setText(f"Łącznie: {total} pracowników")
            self.active_label.setText(f"Aktywni: {active}")
            self.drivers_label.setText(f"Kierowcy: {drivers}")
            
        except Exception as e:
            print(f"Błąd statystyk: {e}")
    
    def add_employee(self):
        """Dodaje nowego pracownika"""
        if not self.validate_form():
            return
        
        conn = self.get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO employees 
                (first_name, last_name, position, department, permissions, email, phone, is_active, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                self.first_name.text().strip(),
                self.last_name.text().strip(),
                self.position.text().strip(),
                self.department.currentText(),
                self.permissions.currentText(),
                self.email.text().strip(),
                self.phone.text().strip(),
                1 if self.is_active.isChecked() else 0,
                self.notes.toPlainText().strip()
            ))
            
            conn.commit()
            QMessageBox.information(self, "Sukces", "Pracownik został dodany!")
            
            self.load_employees()
            self.clear_form()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd dodawania:\n{str(e)}")
        finally:
            conn.close()
    
    def update_employee(self):
        """Aktualizuje pracownika"""
        if not self.employee_id.text():
            QMessageBox.warning(self, "Błąd", "Wybierz pracownika do edycji!")
            return
        
        if not self.validate_form():
            return
        
        conn = self.get_connection()
        if not conn:
            return
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE employees 
                SET first_name = ?, last_name = ?, position = ?, department = ?,
                    permissions = ?, email = ?, phone = ?, is_active = ?, notes = ?
                WHERE id = ?
            """, (
                self.first_name.text().strip(),
                self.last_name.text().strip(),
                self.position.text().strip(),
                self.department.currentText(),
                self.permissions.currentText(),
                self.email.text().strip(),
                self.phone.text().strip(),
                1 if self.is_active.isChecked() else 0,
                self.notes.toPlainText().strip(),
                int(self.employee_id.text())
            ))
            
            conn.commit()
            QMessageBox.information(self, "Sukces", "Pracownik zaktualizowany!")
            
            self.load_employees()
            self.clear_form()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd aktualizacji:\n{str(e)}")
        finally:
            conn.close()
    
    def delete_selected(self):
        """Usuwa zaznaczonych pracowników"""
        selected_rows = set(index.row() for index in self.table.selectedIndexes())
        
        if not selected_rows:
            QMessageBox.warning(self, "Błąd", "Wybierz pracowników do usunięcia!")
            return
        
        reply = QMessageBox.question(
            self, "Potwierdzenie",
            f"Czy na pewno usunąć {len(selected_rows)} pracowników?",
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
                emp_id = int(self.table.item(row, 0).text())
                cursor.execute("DELETE FROM employees WHERE id = ?", (emp_id,))
            
            conn.commit()
            QMessageBox.information(self, "Sukces", "Pracownicy usunięci!")
            
            self.load_employees()
            
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Błąd usuwania:\n{str(e)}")
        finally:
            conn.close()
    
    def load_employee_to_form(self, index):
        """Ładuje dane pracownika do formularza"""
        row = index.row()
        
        self.employee_id.setText(self.table.item(row, 0).text())
        self.first_name.setText(self.table.item(row, 1).text())
        self.last_name.setText(self.table.item(row, 2).text())
        self.position.setText(self.table.item(row, 3).text())
        
        # Ustawienie comboboxów
        dept = self.table.item(row, 4).text()
        idx = self.department.findText(dept)
        if idx >= 0:
            self.department.setCurrentIndex(idx)
        else:
            self.department.setCurrentText(dept)
        
        perm = self.table.item(row, 5).text()
        idx = self.permissions.findText(perm)
        if idx >= 0:
            self.permissions.setCurrentIndex(idx)
        
        self.email.setText(self.table.item(row, 6).text())
        self.phone.setText(self.table.item(row, 7).text())
        
        # Status
        status_text = self.table.item(row, 8).text()
        self.is_active.setChecked(status_text == "Aktywny")
        
        self.add_button.setEnabled(False)
        self.update_button.setEnabled(True)
    
    def clear_form(self):
        """Czyści formularz"""
        self.employee_id.clear()
        self.first_name.clear()
        self.last_name.clear()
        self.position.clear()
        self.department.setCurrentIndex(0)
        self.permissions.setCurrentIndex(0)
        self.email.clear()
        self.phone.clear()
        self.is_active.setChecked(True)
        self.notes.clear()
        
        self.add_button.setEnabled(True)
        self.update_button.setEnabled(False)
    
    def validate_form(self):
        """Waliduje formularz"""
        errors = []
        
        if not self.first_name.text().strip():
            errors.append("Imię jest wymagane")
        
        if not self.last_name.text().strip():
            errors.append("Nazwisko jest wymagane")
        
        if not self.position.text().strip():
            errors.append("Stanowisko jest wymagane")
        
        if errors:
            QMessageBox.warning(self, "Błąd walidacji", "\n".join(errors))
            return False
        
        return True

if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    window = EmployeeWindow()
    window.setWindowTitle("Test - Zarządzanie Pracownikami")
    window.resize(1200, 600)
    window.show()
    sys.exit(app.exec())