from src.services import vehicle_service, employee_service
from src.initialize_database import initialize_database
import sys
import os

# Dodaj ścieżkę główną projektu do sys.path, aby umożliwić importy z `src`
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))


# Inicjalizuj bazę, jeśli to konieczne
initialize_database()

# Sprawdź, czy pojazdy już istnieją
if not vehicle_service.get_all_vehicles():
    print("Dodawanie przykładowych pojazdów...")
    vehicle_service.add_vehicle("Skoda Octavia", "W0 KILER", 125000, 7.8)
    vehicle_service.add_vehicle("Fiat Ducato", "W1 BUS", 210000, 11.2)
    print("Pojazdy dodane.")
else:
    print("Pojazdy już istnieją w bazie.")

# Sprawdź, czy pracownicy już istnieją
if not employee_service.get_all_employees():
    print("Dodawanie przykładowych pracowników...")
    employee_service.add_employee("Jan", "Kowalski")
    employee_service.add_employee("Adam", "Nowak")
    print("Pracownicy dodani.")
else:
    print("Pracownicy już istnieją w bazie.")
