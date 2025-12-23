from src.database import get_db_connection
from datetime import datetime

class FleetError(Exception):
    """Niestandardowy wyjątek dla błędów logiki biznesowej."""
    pass

def get_open_road_card_for_vehicle(vehicle_id: int):
    """Pobiera otwartą kartę drogową dla danego pojazdu. Zwraca None, jeśli nie ma otwartej karty."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM road_cards WHERE vehicle_id = ? AND status = 'OTWARTA'",
        (vehicle_id,)
    )
    card_row = cursor.fetchone()
    conn.close()
    return dict(card_row) if card_row else None

def checkout_vehicle(vehicle_id: int, employee_id: int):
    """
    Logika pobrania pojazdu.
    1. Sprawdza, czy pojazd jest dostępny.
    2. Tworzy nową kartę drogową ('OTWARTA').
    3. Tworzy wpis w logu kluczy ('POBRANIE').
    4. Zmienia status pojazdu na 'W_TRASIE'.
    Wszystko w jednej transakcji.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Krok 1: Sprawdź status pojazdu i pobierz jego dane
        cursor.execute("SELECT status, mileage FROM vehicles WHERE id = ?", (vehicle_id,))
        vehicle_data = cursor.fetchone()

        if not vehicle_data or vehicle_data['status'] != 'W_FIRMIE':
            raise FleetError("Pojazd nie jest dostępny do pobrania.")

        start_mileage = vehicle_data['mileage']

        # Krok 2: Utwórz nową kartę drogową
        start_date = datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO road_cards (vehicle_id, employee_id, status, start_mileage, start_date) VALUES (?, ?, ?, ?, ?)",
            (vehicle_id, employee_id, 'OTWARTA', start_mileage, start_date)
        )
        road_card_id = cursor.lastrowid

        # Krok 3: Dodaj wpis do logu kluczy
        cursor.execute(
            "INSERT INTO keys_log (road_card_id, action, timestamp) VALUES (?, ?, ?)",
            (road_card_id, 'POBRANIE', datetime.now().isoformat())
        )

        # Krok 4: Zaktualizuj status pojazdu
        cursor.execute("UPDATE vehicles SET status = 'W_TRASIE' WHERE id = ?", (vehicle_id,))

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def return_vehicle(road_card_id: int, end_mileage: float):
    """
    Logika zwrotu pojazdu.
    1. Waliduje przebieg końcowy.
    2. Zamyka kartę drogową ('ZAMKNIETA').
    3. Tworzy wpis w logu kluczy ('ZWROT').
    4. Aktualizuje główny przebieg pojazdu.
    5. Zmienia status pojazdu na 'W_FIRMIE'.
    Wszystko w jednej transakcji.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Pobierz dane karty drogowej
        cursor.execute("SELECT vehicle_id, start_mileage FROM road_cards WHERE id = ?", (road_card_id,))
        card_data = cursor.fetchone()

        if not card_data:
            raise FleetError("Nie znaleziono karty drogowej.")

        # Krok 1: Walidacja przebiegu
        if end_mileage < card_data['start_mileage']:
            raise FleetError("Przebieg końcowy nie może być mniejszy niż początkowy.")

        # Krok 2: Zamknij kartę drogową
        end_date = datetime.now().isoformat()
        cursor.execute(
            "UPDATE road_cards SET end_mileage = ?, end_date = ?, status = 'ZAMKNIETA' WHERE id = ?",
            (end_mileage, end_date, road_card_id)
        )

        # Krok 3: Dodaj wpis do logu kluczy
        cursor.execute(
            "INSERT INTO keys_log (road_card_id, action, timestamp) VALUES (?, ?, ?)",
            (road_card_id, 'ZWROT', datetime.now().isoformat())
        )

        # Krok 4 & 5: Zaktualizuj przebieg i status pojazdu
        vehicle_id = card_data['vehicle_id']
        cursor.execute(
            "UPDATE vehicles SET mileage = ?, status = 'W_FIRMIE' WHERE id = ?",
            (end_mileage, vehicle_id)
        )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
