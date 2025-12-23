import unittest
from unittest.mock import patch
import os
import sqlite3

# Import serwisu, który będziemy testować
from src.services import vehicle_service
from src.models.vehicle import Vehicle
from src import database # Importujemy moduł, aby móc go "patchować"

class TestVehicleService(unittest.TestCase):

    TEST_DB_FILE = "test_fleet.db"

    def setUp(self):
        """
        Konfiguracja przed każdym testem.
        Tworzy tymczasową, plikową bazę danych na potrzeby testu.
        """
        # Patchujemy ścieżkę do bazy danych w module `database`, aby wskazywała na nasz plik testowy
        self.db_file_patcher = patch.object(database, 'DATABASE_FILE', self.TEST_DB_FILE)
        self.db_file_patcher.start()

        # Tworzymy i inicjalizujemy schemat w testowej bazie danych
        # get_db_connection() połączy się już z właściwym plikiem testowym dzięki patchowaniu
        conn = database.get_db_connection()
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'database_schema.sql')
        with open(schema_path, 'r') as f:
            schema = f.read()
            conn.cursor().executescript(schema)
        conn.commit()
        conn.close()

    def tearDown(self):
        """
        Sprzątanie po każdym teście.
        Zatrzymuje patchowanie i usuwa plik testowej bazy danych.
        """
        self.db_file_patcher.stop()
        if os.path.exists(self.TEST_DB_FILE):
            os.remove(self.TEST_DB_FILE)

    def test_add_and_get_vehicle(self):
        """
        Testuje dodawanie i pobieranie pojazdu.
        """
        # Dane testowego pojazdu
        test_name = "Testowy Opel"
        test_reg = "WPR TEST"
        test_mileage = 150000.0
        test_consumption = 7.5

        # 1. Dodaj pojazd używając serwisu.
        #    Funkcja `add_vehicle` użyje `get_db_connection`, która połączy się
        #    z naszą testową bazą danych dzięki patchowaniu.
        vehicle_service.add_vehicle(test_name, test_reg, test_mileage, test_consumption)

        # 2. Pobierz wszystkie pojazdy
        vehicles = vehicle_service.get_all_vehicles()

        # 3. Weryfikacja
        self.assertEqual(len(vehicles), 1, "Powinien być dokładnie jeden pojazd w bazie")

        added_vehicle = vehicles[0]
        self.assertIsInstance(added_vehicle, Vehicle)
        self.assertEqual(added_vehicle.name, test_name)
        self.assertEqual(added_vehicle.registration_number, test_reg)
        self.assertEqual(added_vehicle.status, "W_FIRMIE") # Domyślny status
        self.assertEqual(added_vehicle.mileage, test_mileage)
        self.assertEqual(added_vehicle.fuel_consumption, test_consumption)


if __name__ == '__main__':
    unittest.main()
