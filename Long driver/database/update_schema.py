# -*- coding: utf-8 -*-
"""
Dodaje nowe kolumny do tabeli trips dla karty drogowej
"""

import sqlite3
from pathlib import Path

def update_trips_schema():
    """Dodaje brakuj¹ce kolumny do tabeli trips"""
    
    db_path = Path("database/fleet.db")
    
    if not db_path.exists():
        print("? Baza danych nie istnieje!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("??? Aktualizujê schemat tabeli trips...")
        
        # Lista nowych kolumn do dodania
        new_columns = [
            ('trip_number', 'TEXT UNIQUE'),
            ('start_location', 'TEXT NOT NULL DEFAULT ""'),
            ('end_location', 'TEXT'),
            ('destination', 'TEXT NOT NULL DEFAULT ""'),
            ('purpose', 'TEXT'),
            ('daily_distance', 'REAL'),
            ('total_distance', 'REAL'),
            ('start_fuel', 'REAL NOT NULL DEFAULT 0'),
            ('end_fuel', 'REAL'),
            ('fuel_used', 'REAL'),
            ('fuel_cost', 'REAL'),
            ('fuel_type', 'TEXT'),
            ('avg_consumption', 'REAL'),
            ('toll_costs', 'REAL DEFAULT 0'),
            ('other_costs', 'REAL DEFAULT 0'),
            ('total_costs', 'REAL DEFAULT 0'),
            ('driver_license', 'TEXT'),
            ('driver_signature', 'TEXT'),
            ('status', 'TEXT DEFAULT "active"')
        ]
        
        # SprawdŸ które kolumny ju¿ istniej¹
        cursor.execute('PRAGMA table_info(trips)')
        existing_columns = [col[1] for col in cursor.fetchall()]
        
        # Dodaj brakuj¹ce kolumny
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f'ALTER TABLE trips ADD COLUMN {column_name} {column_type}')
                    print(f"? Dodano kolumnê: {column_name}")
                except Exception as e:
                    print(f"? B³¹d dodawania kolumny {column_name}: {e}")
        
        # Utwórz indeksy jeœli nie istniej¹
        indexes = [
            ('idx_trips_status', 'CREATE INDEX IF NOT EXISTS idx_trips_status ON trips(status)'),
            ('idx_trips_number', 'CREATE INDEX IF NOT EXISTS idx_trips_number ON trips(trip_number)')
        ]
        
        for idx_name, idx_query in indexes:
            try:
                cursor.execute(idx_query)
                print(f"? Utworzono indeks: {idx_name}")
            except:
                print(f"?? Indeks {idx_name} ju¿ istnieje")
        
        # Generuj numery kart dla istniej¹cych przejazdów
        cursor.execute("""
            UPDATE trips 
            SET trip_number = 'KD-' || substr('00000' || id, -5) 
            WHERE trip_number IS NULL
        """)
        
        # Dodaj brakuj¹c¹ kolumnê w tabeli vehicles
        try:
            cursor.execute("ALTER TABLE vehicles ADD COLUMN fuel_type TEXT DEFAULT 'Benzyna'")
            print("? Dodano kolumnê fuel_type do vehicles")
        except:
            print("?? Kolumna fuel_type ju¿ istnieje w vehicles")
        
        conn.commit()
        conn.close()
        
        print("\n? Schemat tabeli trips zosta³ zaktualizowany!")
        print("   Dodano wszystkie pola karty drogowej.")
        return True
        
    except Exception as e:
        print(f"? B³¹d aktualizacji schematu: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    update_trips_schema()