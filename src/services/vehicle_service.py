from src.database import get_db_connection
from src.models.vehicle import Vehicle

def add_vehicle(name: str, registration_number: str, mileage: float, fuel_consumption: float):
    """Dodaje nowy pojazd do bazy danych."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO vehicles (name, registration_number, status, mileage, fuel_consumption) VALUES (?, ?, ?, ?, ?)",
        (name, registration_number, 'W_FIRMIE', mileage, fuel_consumption)
    )
    conn.commit()
    conn.close()

def get_all_vehicles() -> list[Vehicle]:
    """Pobiera wszystkie pojazdy z bazy danych."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vehicles")
    vehicles_rows = cursor.fetchall()
    conn.close()

    return [Vehicle(**dict(row)) for row in vehicles_rows]

def update_vehicle_status(vehicle_id: int, new_status: str):
    """Aktualizuje status pojazdu."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE vehicles SET status = ? WHERE id = ?",
        (new_status, vehicle_id)
    )
    conn.commit()
    conn.close()
