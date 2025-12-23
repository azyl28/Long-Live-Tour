from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from src.services import fleet_service
from src.models.vehicle import Vehicle

class ReturnDialog(QDialog):
    def __init__(self, vehicle: Vehicle, road_card_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zwrot pojazdu")
        self.vehicle = vehicle
        self.road_card_id = road_card_id

        self.layout = QVBoxLayout(self)

        # Etykiety informacyjne
        self.layout.addWidget(QLabel(f"<b>Pojazd:</b> {self.vehicle.name} ({self.vehicle.registration_number})"))
        self.layout.addWidget(QLabel(f"<b>Przebieg przy pobraniu:</b> {self.vehicle.mileage} km"))

        # Pole do wpisania przebiegu
        self.layout.addWidget(QLabel("Wpisz przebieg końcowy:"))
        self.mileage_input = QLineEdit()
        self.layout.addWidget(self.mileage_input)

        # Przyciski
        self.confirm_button = QPushButton("Zatwierdź zwrot")
        self.confirm_button.clicked.connect(self.accept_return)
        self.cancel_button = QPushButton("Anuluj")
        self.cancel_button.clicked.connect(self.reject)

        self.layout.addWidget(self.confirm_button)
        self.layout.addWidget(self.cancel_button)

    def accept_return(self):
        """Obsługuje logikę zatwierdzenia zwrotu."""
        end_mileage_str = self.mileage_input.text().strip()
        if not end_mileage_str:
            QMessageBox.warning(self, "Błąd", "Przebieg końcowy nie może być pusty.")
            return

        try:
            end_mileage = float(end_mileage_str)
        except ValueError:
            QMessageBox.warning(self, "Błąd", "Przebieg musi być liczbą.")
            return

        try:
            fleet_service.return_vehicle(self.road_card_id, end_mileage)
            QMessageBox.information(self, "Sukces", "Pojazd został pomyślnie zwrócony.")
            self.accept()
        except fleet_service.FleetError as e:
            QMessageBox.critical(self, "Błąd logiki", str(e))
        except Exception as e:
            QMessageBox.critical(self, "Błąd operacji", f"Wystąpił błąd: {e}")
            self.reject()
