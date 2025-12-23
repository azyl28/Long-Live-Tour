import sqlite3
import os

# Definicja ścieżki do bazy danych
DATABASE_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'fleet.db')

def get_db_connection():
    """
    Tworzy i zwraca połączenie z bazą danych SQLite.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # Umożliwia dostęp do kolumn przez ich nazwy
    return conn
