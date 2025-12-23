# -*- coding: utf-8 -*-
"""
Główny plik aplikacji - System Ewidencji Pojazdów
"""

import sys
import os
from pathlib import Path
import sqlite3

# Dodaj ścieżkę src do PYTHONPATH
sys.path.append(str(Path(__file__).parent / 'src'))

from PySide6.QtWidgets import QApplication

def fix_distance_column_on_startup():
    """
    Sprawdza i naprawia kolumnę 'distance' w tabeli 'trips'
    podczas uruchamiania aplikacji, jeśli jest ona typu 'GENERATED'.
    """
    db_path = Path(__file__).parent / "database" / "fleet.db"
    if not db_path.exists():
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='trips'")
        result = cursor.fetchone()
        if not result:
            conn.close()
            return

        schema_sql = result[0].upper()
        distance_is_generated = 'DISTANCE' in schema_sql and 'GENERATED' in schema_sql

        if not distance_is_generated:
            conn.close()
            return

        print("⚠️ Wykryto przestarzałą strukturę tabeli 'trips'. Rozpoczynam naprawę kolumny 'distance'...")

        # Zmień nazwę starej tabeli
        cursor.execute("ALTER TABLE trips RENAME TO trips_old")

        # Utwórz nową tabelę na podstawie schema.sql
        schema_path = Path(__file__).parent / 'database' / 'schema.sql'
        if not schema_path.exists():
             raise FileNotFoundError(f"Schema file not found: {schema_path}")

        with open(schema_path, 'r', encoding='utf-8') as f:
            new_schema_sql = f.read()

        # Usuń polecenia tworzenia indeksów na razie
        new_schema_sql = new_schema_sql.split("CREATE INDEX")[0]

        cursor.execute(new_schema_sql)

        # Skopiuj dane ze starej tabeli do nowej
        cursor.execute("PRAGMA table_info(trips_old)")
        source_columns = [col[1] for col in cursor.fetchall() if col[1].lower() != 'distance']

        target_columns = source_columns.copy()
        if 'distance' not in target_columns:
             target_columns.append('distance')

        source_columns_str = ', '.join(f'"{c}"' for c in source_columns)
        target_columns_str = ', '.join(f'"{c}"' for c in target_columns)

        cursor.execute(f"""
            INSERT INTO trips ({target_columns_str})
            SELECT {source_columns_str},
                   CASE
                       WHEN end_mileage IS NOT NULL AND start_mileage IS NOT NULL
                       THEN end_mileage - start_mileage
                       ELSE NULL
                   END
            FROM trips_old
        """)

        # Usuń starą tabelę
        cursor.execute("DROP TABLE trips_old")

        # Ponownie utwórz indeksy
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_dates ON trips(start_date, end_date);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_status ON trips(status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_vehicle ON trips(vehicle_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_employee ON trips(employee_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_trips_number ON trips(trip_number);")

        conn.commit()
        print("✅ Struktura tabeli 'trips' została pomyślnie naprawiona.")

    except sqlite3.Error as e:
        print(f"❌ Błąd podczas naprawy bazy danych: {e}")
        if 'conn' in locals() and conn:
            conn.rollback()
    finally:
        if 'conn' in locals() and conn:
            conn.close()

def sprawdz_baze_danych():
    """Sprawdza czy baza danych istnieje i naprawia jej strukturę w razie potrzeby."""
    sciezka_bazy = Path("database/fleet.db")
    if not sciezka_bazy.exists():
        print("❌ Baza danych nie istnieje!")
        print("Uruchom: python database\\init_database.py")
        return False

    fix_distance_column_on_startup()
    return True

def main():
    print("=" * 50)
    print("Uruchamianie Systemu Ewidencji Pojazdów")
    print("=" * 50)
    
    # Sprawdź bazę danych
    if not sprawdz_baze_danych():
        return 1
    
    # Załaduj główne okno
    try:
        from src.gui.main_window import MainWindow
        print("✅ Moduły GUI załadowane pomyślnie")
    except ImportError as e:
        print(f"❌ Błąd importu: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Uruchom aplikację Qt
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("System Ewidencji Pojazdów")
        app.setApplicationDisplayName("Long Driver - System Zarządzania Pojazdami")
        
        window = MainWindow()
        window.show()
        
        print("\n" + "=" * 50)
        print("✅ Aplikacja uruchomiona pomyślnie!")
        print("=" * 50)
        
        return app.exec()
        
    except Exception as e:
        print(f"❌ Błąd aplikacji: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())