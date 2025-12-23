from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QMessageBox
from src.services import vehicle_service, employee_service, fleet_service
from src.gui.checkout_dialog import CheckoutDialog
from src.gui.return_dialog import ReturnDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("System Ewidencji Pojazdów")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.vehicle_table = QTableWidget()
        self.vehicle_table.setColumnCount(5)
        self.vehicle_table.setHorizontalHeaderLabels(["ID", "Nazwa", "Rejestracja", "Status", "Przebieg"])
        layout.addWidget(self.vehicle_table)

        self.checkout_button = QPushButton("Pobierz pojazd")
        self.checkout_button.clicked.connect(self.open_checkout_dialog)
        self.return_button = QPushButton("Zwróć pojazd")
        self.return_button.clicked.connect(self.open_return_dialog) # Połączenie sygnału
        layout.addWidget(self.checkout_button)
        layout.addWidget(self.return_button)

        self.load_vehicles()

    def load_vehicles(self):
        """Pobiera pojazdy z serwisu i wyświetla je w tabeli."""
        vehicles = vehicle_service.get_all_vehicles()
        self.vehicle_table.setRowCount(len(vehicles))

        for row, vehicle in enumerate(vehicles):
            self.vehicle_table.setItem(row, 0, QTableWidgetItem(str(vehicle.id)))
            self.vehicle_table.setItem(row, 1, QTableWidgetItem(vehicle.name))
            self.vehicle_table.setItem(row, 2, QTableWidgetItem(vehicle.registration_number))
            self.vehicle_table.setItem(row, 3, QTableWidgetItem(vehicle.status))
            self.vehicle_table.setItem(row, 4, QTableWidgetItem(str(vehicle.mileage)))

    def open_checkout_dialog(self):
        """Otwiera dialog pobrania pojazdu."""
        selected_vehicle = self._get_selected_vehicle_data()
        if not selected_vehicle:
            return

        if selected_vehicle.status != 'W_FIRMIE':
            QMessageBox.warning(self, "Błąd", "Można pobrać tylko pojazd, który jest 'W FIRMIE'.")
            return

        employees = employee_service.get_all_employees()
        dialog = CheckoutDialog(selected_vehicle, employees, self)

        if dialog.exec():
            self.load_vehicles()

    def open_return_dialog(self):
        """Otwiera dialog zwrotu pojazdu."""
        selected_vehicle = self._get_selected_vehicle_data()
        if not selected_vehicle:
            return

        if selected_vehicle.status != 'W_TRASIE':
            QMessageBox.warning(self, "Błąd", "Można zwrócić tylko pojazd, który jest 'W TRASIE'.")
            return

        # Znajdź otwartą kartę drogową dla tego pojazdu
        open_card = fleet_service.get_open_road_card_for_vehicle(selected_vehicle.id)
        if not open_card:
            QMessageBox.critical(self, "Błąd krytyczny", "Nie znaleziono otwartej karty drogowej dla tego pojazdu!")
            return

        dialog = ReturnDialog(selected_vehicle, open_card['id'], self)

        if dialog.exec():
            self.load_vehicles() # Odśwież po udanym zwrocie

    def _get_selected_vehicle_data(self):
        """Pobiera pełny obiekt Vehicle dla zaznaczonego wiersza."""
        selected_rows = self.vehicle_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Błąd", "Najpierw zaznacz pojazd z listy.")
            return None

        selected_row = selected_rows[0].row()
        vehicle_id = int(self.vehicle_table.item(selected_row, 0).text())

        all_vehicles = vehicle_service.get_all_vehicles()
        selected_vehicle = next((v for v in all_vehicles if v.id == vehicle_id), None)

        if not selected_vehicle:
            QMessageBox.critical(self, "Błąd krytyczny", "Nie znaleziono danych wybranego pojazdu.")
            return None

        return selected_vehicle
