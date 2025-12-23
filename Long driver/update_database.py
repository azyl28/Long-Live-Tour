# -*- coding: utf-8 -*-
"""
Prosty skrypt do aktualizacji istniejącej bazy fleet.db:
- dodaje kolumny refuel_liters i refuel_invoice do tabeli trips (jeśli ich nie ma)
"""

import sqlite3
from pathlib import Path


def update_database(db_path: str) -> None:
    db_file = Path(db_path)

    if not db_file.exists():
        print(f"Baza nie istnieje: {db_file.resolve()}")
        return

    conn = sqlite3.connect(db_file)
    try:
        cursor = conn.cursor()

        # Sprawdź istniejące kolumny w trips
        cursor.execute("PRAGMA table_info(trips);")
        columns = {row[1] for row in cursor.fetchall()}

        # Dodaj kolumny tylko jeśli ich nie ma
        if "refuel_liters" not in columns:
            cursor.execute(
                "ALTER TABLE trips ADD COLUMN refuel_liters REAL;"
            )
            print("Dodano kolumnę: trips.refuel_liters")

        if "refuel_invoice" not in columns:
            cursor.execute(
                "ALTER TABLE trips ADD COLUMN refuel_invoice TEXT;"
            )
            print("Dodano kolumnę: trips.refuel_invoice")

        conn.commit()
        print("Aktualizacja bazy zakończona pomyślnie.")
    except Exception as e:
        print(f"Błąd aktualizacji bazy: {e}")
    finally:
        conn.close()


def main():
    # Ścieżka jak w init_database.py
    db_path = "database/fleet.db"
    update_database(db_path)


if __name__ == "__main__":
    main()
