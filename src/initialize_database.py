from src.database import get_db_connection
import os

def initialize_database():
    """
    Inicjalizuje bazę danych, tworząc ją na podstawie schematu, jeśli nie istnieje.
    """
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fleet.db')
    schema_path = os.path.join(os.path.dirname(__file__), 'database_schema.sql')

    # Utwórz bazę danych tylko jeśli plik nie istnieje
    if not os.path.exists(db_path):
        print("Tworzenie nowej bazy danych...")
        conn = get_db_connection()
        cursor = conn.cursor()

        with open(schema_path, 'r') as f:
            schema = f.read()
            cursor.executescript(schema)

        conn.commit()
        conn.close()
        print("Baza danych została pomyślnie utworzona.")
    else:
        print("Baza danych już istnieje.")

if __name__ == '__main__':
    initialize_database()
