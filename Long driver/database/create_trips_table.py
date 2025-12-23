# -*- coding: utf-8 -*-
"""
Utworzenie tabeli trips
"""

import sqlite3
from pathlib import Path

def create_trips_table():
    """Tworzy tabelę trips jeśli nie istnieje"""
    
    db_path = Path("database/fleet.db")
    
    if not db_path.exists():
        print("❌ Baza danych nie istnieje!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🛠️ Tworzę tabelę trips...")
        
        # Utwórz tabelę trips
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP,
                start_mileage REAL,
                end_mileage REAL,
                purpose TEXT,
                notes TEXT,
                distance REAL,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)
        
        # Utwórz indeksy
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_dates ON trips(start_date, end_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_vehicle ON trips(vehicle_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_employee ON trips(employee_id)")
        
        conn.commit()
        conn.close()
        
        print("✅ Tabela trips została utworzona!")
        return True
        
    except Exception as e:
        print(f"❌ Błąd tworzenia tabeli: {e}")
        return False

if __name__ == "__main__":
    create_trips_table()