from PySide6.QtWidgets import QDialog, QVBoxLayout, QComboBox, QLabel, QPushButton, QMessageBox
from src.services import fleet_service
from src.models.vehicle import Vehicle
from src.models.employee import Employee

class CheckoutDialog(QDialog):
    def __init__(self, vehicle: Vehicle, employees: list[Employee], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pobranie pojazdu")
        self.vehicle = vehicle
        self.employees = employees

        self.layout = QVBoxLayout(self)

        # Etykiety informacyjne
        self.layout.addWidget(QLabel(f"<b>Pojazd:</b> {self.vehicle.name} ({self.vehicle.registration_number})"))
        self.layout.addWidget(QLabel(f"<b>Aktualny przebieg:</b> {self.vehicle.mileage} km"))

        # Lista rozwijana z pracownikami
        self.layout.addWidget(QLabel("Wybierz pracownika:"))
        self.employee_combo = QComboBox()
        for emp in self.employees:
            self.employee_combo.addItem(f"{emp.first_name} {emp.last_name}", userData=emp.id)
        self.layout.addWidget(self.employee_combo)

        # Przyciski
        self.confirm_button = QPushButton("Zatwierdź pobranie")
        self.confirm_button.clicked.connect(self.accept_checkout)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)

        self.layout.addWidget(self.confirm_button)
        self.layout.addWidget(self.cancel_button)

    def accept_checkout(self):
        """Obsługuje logikę zatwierdzenia pobrania."""
        employee_id = self.employee_combo.currentData()
        if not employee_id:
            QMessageBox.warning(self, "Błąd", "Nie wybrano pracownika.")
            return

        try:
            fleet_service.checkout_vehicle(self.vehicle.id, employee_id)
            QMessageBox.information(self, "Sukces", "Pojazd został pomyślnie pobrany.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Błąd operacji", f"Wystąpił błąd: {e}")
            self.reject()
