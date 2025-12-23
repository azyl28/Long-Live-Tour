import unittest
import os
import sqlite3
from unittest.mock import patch
from src import database
from src.services import fleet_service, vehicle_service

class TestFleetService(unittest.TestCase):

    TEST_DB_FILE = "test_fleet_service.db"

    def setUp(self):
        """Konfiguracja przed każdym testem."""
        self.db_file_patcher = patch.object(database, 'DATABASE_FILE', self.TEST_DB_FILE)
        self.db_file_patcher.start()

        conn = database.get_db_connection()
        schema_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'database_schema.sql')
        with open(schema_path, 'r') as f:
            schema = f.read()
            conn.cursor().executescript(schema)

        # Dodajmy dane testowe
        cursor = conn.cursor()
        cursor.execute("INSERT INTO employees (first_name, last_name) VALUES (?, ?)", ("Jan", "Kowalski"))
        self.test_employee_id = cursor.lastrowid

        cursor.execute(
            "INSERT INTO vehicles (name, registration_number, status, mileage, fuel_consumption) VALUES (?, ?, ?, ?, ?)",
            ("Opel Astra", "WPR 12345", "W_FIRMIE", 100000.0, 6.5)
        )
        self.test_vehicle_id = cursor.lastrowid

        conn.commit()
        conn.close()

    def tearDown(self):
        """Sprzątanie po każdym teście."""
        self.db_file_patcher.stop()
        if os.path.exists(self.TEST_DB_FILE):
            os.remove(self.TEST_DB_FILE)

    def test_checkout_and_return_flow(self):
        """Testuje pełny cykl pobrania i zwrotu pojazdu."""
        # --- FAZA 1: POBRANIE POJAZDU ---
        initial_mileage = 100000.0
        fleet_service.checkout_vehicle(self.test_vehicle_id, self.test_employee_id)

        # Weryfikacja po pobraniu
        conn = database.get_db_connection()
        cursor = conn.cursor()

        # Sprawdź status pojazdu
        cursor.execute("SELECT status FROM vehicles WHERE id = ?", (self.test_vehicle_id,))
        vehicle_status = cursor.fetchone()['status']
        self.assertEqual(vehicle_status, "W_TRASIE")

        # Sprawdź, czy istnieje otwarta karta drogowa
        cursor.execute("SELECT * FROM road_cards WHERE vehicle_id = ? AND status = ?", (self.test_vehicle_id, "OTWARTA"))
        open_card = cursor.fetchone()
        self.assertIsNotNone(open_card)
        self.assertEqual(open_card['start_mileage'], initial_mileage)

        # Sprawdź log kluczy
        cursor.execute("SELECT action FROM keys_log WHERE road_card_id = ?", (open_card['id'],))
        key_log_action = cursor.fetchone()['action']
        self.assertEqual(key_log_action, "POBRANIE")

        conn.close()

        # --- FAZA 2: PRÓBA PONOWNEGO POBRANIA (OCZEKIWANY BŁĄD) ---
        with self.assertRaises(fleet_service.FleetError, msg="Nie można pobrać pojazdu, który jest w trasie"):
            fleet_service.checkout_vehicle(self.test_vehicle_id, self.test_employee_id)

        # --- FAZA 3: ZWROT POJAZDU ---
        road_card_id_to_return = open_card['id']
        end_mileage = 100250.5

        # Próba zwrotu z nieprawidłowym przebiegiem
        with self.assertRaises(fleet_service.FleetError, msg="Przebieg końcowy nie może być mniejszy niż początkowy"):
            fleet_service.return_vehicle(road_card_id_to_return, 99999.0)

        # Poprawny zwrot
        fleet_service.return_vehicle(road_card_id_to_return, end_mileage)

        # Weryfikacja po zwrocie
        conn = database.get_db_connection()
        cursor = conn.cursor()

        # Sprawdź status i przebieg pojazdu
        cursor.execute("SELECT status, mileage FROM vehicles WHERE id = ?", (self.test_vehicle_id,))
        vehicle_data = cursor.fetchone()
        self.assertEqual(vehicle_data['status'], "W_FIRMIE")
        self.assertEqual(vehicle_data['mileage'], end_mileage)

        # Sprawdź, czy karta została zamknięta
        cursor.execute("SELECT status FROM road_cards WHERE id = ?", (road_card_id_to_return,))
        card_status = cursor.fetchone()['status']
        self.assertEqual(card_status, "ZAMKNIETA")

        # Sprawdź log kluczy
        cursor.execute("SELECT COUNT(*) FROM keys_log WHERE road_card_id = ? AND action = ?", (road_card_id_to_return, "ZWROT"))
        log_count = cursor.fetchone()[0]
        self.assertEqual(log_count, 1, "Powinien być jeden wpis ZWROT w logu kluczy")

        conn.close()

if __name__ == '__main__':
    unittest.main()
