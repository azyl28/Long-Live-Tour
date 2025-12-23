# -*- coding: utf-8 -*-
"""
Główne okno aplikacji
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QTabWidget, QMessageBox,
    QGridLayout, QGroupBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QAction


class MainWindow(QMainWindow):
    """Główne okno aplikacji System Ewidencji Pojazdów"""

    def __init__(self):
        super().__init__()

        self.vehicle_window = None
        self.employee_window = None
        self.key_window = None
        self.trip_window = None
        self.reports_window = None

        self.setup_ui()
        self.setup_menu()

    # ================== UI ==================

    def setup_ui(self):
        """Konfiguruje interfejs użytkownika"""
        self.setWindowTitle("System Ewidencji Pojazdów - Long Driver v1.0")
        self.setGeometry(100, 100, 1400, 900)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        header_label = QLabel("🚗 SYSTEM EWIDENCJI POJAZDÓW - LONG DRIVER")
        header_font = QFont()
        header_font.setPointSize(24)
        header_font.setBold(True)
        header_label.setFont(header_font)
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("color: #2c3e50; padding: 20px;")
        main_layout.addWidget(header_label)

        quick_access = self.create_quick_access_panel()
        main_layout.addWidget(quick_access)

        self.tab_widget = QTabWidget()
        self.setup_tabs()
        main_layout.addWidget(self.tab_widget)

        self.statusBar().showMessage("✅ System gotowy do pracy")

    def create_quick_access_panel(self):
        """Tworzy panel szybkiego dostępu"""
        panel = QGroupBox("⚡ Główne akcje")
        panel.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14px; }")
        layout = QGridLayout()

        buttons = {
            "Zarządzanie flotą": [
                ("🛣️ Rozpocznij przejazd", self.new_trip),
                ("📝 Przeglądaj arkusze", self.new_trip_sheet),
                ("🔑 Wypożycz klucz", self.checkout_key),
                ("↩️ Zwróć klucz", self.return_key),
            ],
            "Zarządzanie danymi": [
                ("🚗 Dodaj pojazd", self.add_new_vehicle),
                ("👥 Dodaj pracownika", self.add_new_employee),
                ("📊 Generuj raport", self.generate_report),
                ("⚙️ Ustawienia", self.show_settings),
            ],
        }

        col = 0
        for category, button_list in buttons.items():
            cat_label = QLabel(category)
            cat_label.setAlignment(Qt.AlignCenter)
            cat_font = QFont()
            cat_font.setBold(True)
            cat_label.setFont(cat_font)
            layout.addWidget(cat_label, 0, col, 1, 2)

            for i, (text, slot) in enumerate(button_list):
                btn = QPushButton(text)
                btn.setMinimumHeight(50)
                btn.clicked.connect(slot)
                row = 1 + i // 2
                col_offset = col + (i % 2)
                layout.addWidget(btn, row, col_offset)

            col += 2

        panel.setLayout(layout)
        return panel

    def setup_tabs(self):
        """Konfiguruje zakładki główne"""

        # 0 - Moje pojazdy (od razu VehicleWindow)
        from .vehicle_window import VehicleWindow
        self.vehicle_window = VehicleWindow()
        self.tab_widget.addTab(self.vehicle_window, "🚗 Moje pojazdy")

        # 1 - Pracownicy (załadowani przy pierwszym użyciu)
        self.tab_widget.addTab(QWidget(), "👥 Pracownicy")

        # 2 - Klucze
        self.tab_widget.addTab(QWidget(), "🔑 Klucze")

        # 3 - Przejazdy
        self.tab_widget.addTab(QWidget(), "🛣️ Przejazdy")

        # 4 - Raporty
        self.tab_widget.addTab(QWidget(), "📊 Raporty")

    def setup_menu(self):
        """Konfiguruje menu główne"""

        menubar = self.menuBar()

        # Plik
        file_menu = menubar.addMenu("📁 Plik")

        new_vehicle_action = QAction("🚗 Nowy pojazd", self)
        new_vehicle_action.setShortcut("Ctrl+P")
        new_vehicle_action.triggered.connect(self.add_new_vehicle)
        file_menu.addAction(new_vehicle_action)

        new_employee_action = QAction("👥 Nowy pracownik", self)
        new_employee_action.setShortcut("Ctrl+E")
        new_employee_action.triggered.connect(self.add_new_employee)
        file_menu.addAction(new_employee_action)

        file_menu.addSeparator()

        exit_action = QAction("🚪 Zamknij", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Widok
        view_menu = menubar.addMenu("👁️ Widok")

        view_vehicles_action = QAction("Moje pojazdy", self)
        view_vehicles_action.triggered.connect(self.show_vehicles)
        view_menu.addAction(view_vehicles_action)

        view_employees_action = QAction("Pracownicy", self)
        view_employees_action.triggered.connect(self.show_employees)
        view_menu.addAction(view_employees_action)

        # Pomoc
        help_menu = menubar.addMenu("❓ Pomoc")

        help_action = QAction("Pomoc", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        about_action = QAction("O programie", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # ================== Akcje z przycisków ==================

    def add_new_vehicle(self):
        self.show_vehicles()
        self.statusBar().showMessage("Dodawanie nowego pojazdu...")

    def add_new_employee(self):
        self.show_employees()
        self.statusBar().showMessage("Dodawanie nowego pracownika...")

    # ================== Zakładki: pojazdy / pracownicy ==================

    def show_vehicles(self):
        """Przełącza na zakładkę Moje pojazdy"""
        if self.vehicle_window is None:
            from .vehicle_window import VehicleWindow
            self.vehicle_window = VehicleWindow()
            self.tab_widget.removeTab(0)
            self.tab_widget.insertTab(0, self.vehicle_window, "🚗 Moje pojazdy")
        self.tab_widget.setCurrentIndex(0)
        self.statusBar().showMessage("Przeglądanie pojazdów")

    def show_employees(self):
        """Przełącza na zakładkę pracowników"""
        if self.employee_window is None:
            from .employee_window import EmployeeWindow
            self.employee_window = EmployeeWindow()
            self.tab_widget.removeTab(1)
            self.tab_widget.insertTab(1, self.employee_window, "👥 Pracownicy")
        self.tab_widget.setCurrentIndex(1)
        self.statusBar().showMessage("Przeglądanie pracowników")

    # ================== Klucze / przejazdy / arkusze / raporty ==================

    def checkout_key(self):
        """Moduł wypożyczania kluczy"""
        if self.key_window is None:
            from .key_checkout_window import KeyCheckoutWindow
            self.key_window = KeyCheckoutWindow()
            self.tab_widget.removeTab(2)
            self.tab_widget.insertTab(2, self.key_window, "🔑 Klucze")
        self.tab_widget.setCurrentIndex(2)
        self.statusBar().showMessage("Wypożyczanie klucza...")

    def return_key(self):
        """Moduł zwrotu kluczy (ta sama zakładka)"""
        from .key_return_window import KeyReturnWindow
        self.key_window = KeyReturnWindow()
        self.tab_widget.removeTab(2)
        self.tab_widget.insertTab(2, self.key_window, "🔑 Klucze")
        self.tab_widget.setCurrentIndex(2)
        self.statusBar().showMessage("Zwrot klucza...")

    def new_trip(self):
        """Moduł przejazdów"""
        if self.trip_window is None:
            from .trip_window import TripWindow
            self.trip_window = TripWindow()
            self.tab_widget.removeTab(3)
            self.tab_widget.insertTab(3, self.trip_window, "🛣️ Przejazdy")
        self.tab_widget.setCurrentIndex(3)
        self.statusBar().showMessage("Tworzenie nowego przejazdu...")

    def new_trip_sheet(self):
        """Otwiera moduł arkuszy przejazdów"""
        try:
            from .trip_sheet_window import TripSheetWindow
            if not hasattr(self, "trip_sheet_tab_index"):
                self.trip_sheet_window = TripSheetWindow()
                self.trip_sheet_tab_index = self.tab_widget.addTab(
                    self.trip_sheet_window, "📝 Arkusze przejazdów"
                )
            self.tab_widget.setCurrentIndex(self.trip_sheet_tab_index)
            self.statusBar().showMessage("Przeglądanie arkuszy przejazdów...")
        except ImportError:
            QMessageBox.critical(self, "Błąd", "Nie można załadować modułu arkuszy przejazdów.")

    def generate_report(self):
        """Moduł raportów"""
        if self.reports_window is None:
            from .reports_window import ReportsWindow
            self.reports_window = ReportsWindow()
            self.tab_widget.removeTab(4)
            self.tab_widget.insertTab(4, self.reports_window, "📊 Raporty")
        self.tab_widget.setCurrentIndex(4)
        self.statusBar().showMessage("Generowanie raportu...")

    # ================== Ustawienia ==================

    def show_settings(self):
        """Otwiera zakładkę ustawień"""
        if not hasattr(self, "settings_tab_index"):
            settings_widget = self.create_settings_tab()
            self.settings_tab_index = self.tab_widget.addTab(
                settings_widget, "⚙️ Ustawienia"
            )
        self.tab_widget.setCurrentIndex(self.settings_tab_index)
        self.statusBar().showMessage("Wyświetlono ustawienia")

    def create_settings_tab(self):
        """Tworzy zawartość zakładki ustawień"""
        widget = QWidget()
        layout = QVBoxLayout()
        widget.setLayout(layout)

        reset_group = QGroupBox("Reset aplikacji")
        reset_layout = QVBoxLayout()
        reset_group.setLayout(reset_layout)

        reset_label = QLabel(
            "Przywrócenie ustawień fabrycznych usunie wszystkie dane "
            "(przejazdy, pojazdy, pracowników) i utworzy nową, czystą bazę. "
            "Operacja jest nieodwracalna!"
        )
        reset_label.setWordWrap(True)

        reset_button = QPushButton("RESETUJ APLIKACJĘ")
        reset_button.setStyleSheet(
            "background-color: #c0392b; color: white; font-weight: bold;"
        )
        reset_button.clicked.connect(self.reset_application)

        reset_layout.addWidget(reset_label)
        reset_layout.addWidget(reset_button)

        layout.addWidget(reset_group)
        layout.addStretch()

        return widget

    def reset_application(self):
        """Resetuje aplikację do ustawień fabrycznych"""
        reply = QMessageBox.warning(
            self,
            "Potwierdzenie resetu",
            "Czy na pewno chcesz zresetować aplikację?\n"
            "Wszystkie dane zostaną trwale usunięte!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        try:
            db_path = Path(__file__).parent.parent.parent / "database" / "fleet.db"
            if db_path.exists():
                db_path.unlink()

            from ..database.init_database import DatabaseInitializer
            initializer = DatabaseInitializer(str(db_path))
            initializer.initialize()

            QMessageBox.information(
                self,
                "Sukces",
                "Aplikacja została zresetowana. Uruchom ją ponownie.",
            )
            self.close()
        except Exception as e:
            QMessageBox.critical(self, "Błąd", f"Nie udało się zresetować aplikacji:\n{e}")

    # ================== Pomoc / O programie / Zamknięcie ==================

    def show_help(self):
        QMessageBox.information(
            self,
            "Pomoc - Long Driver",
            "**Wersja:** 1.0.0\n\n"
            "**Działające moduły:**\n"
            "• 🚗 Zarządzanie pojazdami\n"
            "• 👥 Zarządzanie pracownikami\n"
            "• 🔑 Kontrola kluczy\n"
            "• 🛣️ Rejestracja przejazdów\n"
            "• 📊 Generowanie raportów\n\n"
            "**Skróty:**\n"
            "• Ctrl+P - Nowy pojazd\n"
            "• Ctrl+E - Nowy pracownik\n"
            "• F1 - Pomoc\n"
            "• Ctrl+Q - Zamknij"
        )

    def show_about(self):
        QMessageBox.about(
            self,
            "O programie - Long Driver",
            "**Wersja:** 1.0.0\n\n"
            "Kompleksowy system do zarządzania flotą pojazdów.\n\n"
            "Funkcje:\n"
            "• Zarządzanie pojazdami\n"
            "• Zarządzanie pracownikami\n"
            "• Kontrola kluczy\n"
            "• Rejestracja przejazdów\n"
            "• Generowanie raportów\n"
            "• Baza danych SQLite\n\n"
            "Autor: Radek\n"
            "© 2025 - Wszystkie prawa zastrzeżone"
        )

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Potwierdzenie zamknięcia",
            "Czy na pewno chcesz zamknąć aplikację?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            print("🔄 Zamykanie aplikacji...")
            self.statusBar().showMessage("Zamykanie...")
            event.accept()
        else:
            event.ignore()


if __name__ == "__main__":
    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
