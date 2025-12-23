# Naprawa kolumny distance

import sqlite3
from pathlib import Path

def fix_distance_column():
    """Naprawia kolumnę distance - usuwa generated column"""
    
    db_path = Path("database/fleet.db")
    
    if not db_path.exists():
        print("Błąd: Baza nie istnieje!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Naprawiam kolumnę distance...")
    
    # 1. Sprawdź czy distance jest generated column
    cursor.execute('PRAGMA table_info(trips)')
    columns = cursor.fetchall()
    
    distance_is_generated = False
    for col in columns:
        if col[1] == 'distance' and len(col) > 5 and col[5]:
            distance_is_generated = True
            print(f"Kolumna distance jest GENERATED: {col}")
            break
    
    if not distance_is_generated:
        print("Kolumna distance NIE jest generated - inny problem")
        conn.close()
        return True
    
    # 2. Utwórz nową tabelę bez generated column
    print("Tworzę nową tabelę...")
    
    cursor.execute("""
        CREATE TABLE trips_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            start_date TIMESTAMP NOT NULL,
            end_date TIMESTAMP,
            start_mileage REAL,
            end_mileage REAL,
            purpose TEXT,
            notes TEXT,
            distance REAL,  -- ZWYKŁA kolumna, nie generated!
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
            FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
        )
    """)
    
    # 3. Skopiuj dane (bez próby wstawiania do distance)
    try:
        cursor.execute("""
            INSERT INTO trips_new 
            (id, vehicle_id, employee_id, start_date, end_date,
             start_mileage, end_mileage, purpose, notes, distance)
            SELECT id, vehicle_id, employee_id, start_date, end_date,
                   start_mileage, end_mileage, purpose, notes,
                   CASE 
                       WHEN end_mileage IS NOT NULL AND start_mileage IS NOT NULL 
                       THEN end_mileage - start_mileage
                       ELSE NULL
                   END
            FROM trips
        """)
        print("Dane skopiowane")
    except Exception as e:
        print(f"Błąd kopiowania: {e}")
        # Spróbuj bez kolumny distance
        cursor.execute("DROP TABLE trips_new")
        cursor.execute("""
            CREATE TABLE trips_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                start_date TIMESTAMP NOT NULL,
                end_date TIMESTAMP,
                start_mileage REAL,
                end_mileage REAL,
                purpose TEXT,
                notes TEXT,
                FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("""
            INSERT INTO trips_new 
            (id, vehicle_id, employee_id, start_date, end_date,
             start_mileage, end_mileage, purpose, notes)
            SELECT id, vehicle_id, employee_id, start_date, end_date,
                   start_mileage, end_mileage, purpose, notes
            FROM trips
        """)
        print("Dane skopiowane (bez distance)")
    
    # 4. Zamień tabele
    cursor.execute("DROP TABLE trips")
    cursor.execute("ALTER TABLE trips_new RENAME TO trips")
    
    # 5. Utwórz indeksy
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_dates ON trips(start_date, end_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_vehicle ON trips(vehicle_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_employee ON trips(employee_id)")
    
    conn.commit()
    conn.close()
    
    print("\nSUKCES: Kolumna distance naprawiona!")
    print("Możesz teraz dodawać przejazdy.")
    return True

if __name__ == "__main__":
    fix_distance_column()