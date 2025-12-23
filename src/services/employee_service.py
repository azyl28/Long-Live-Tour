from src.database import get_db_connection
from src.models.employee import Employee

def get_all_employees() -> list[Employee]:
    """Pobiera wszystkich pracowników z bazy danych."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM employees")
    employee_rows = cursor.fetchall()
    conn.close()

    return [Employee(**dict(row)) for row in employee_rows]

def add_employee(first_name: str, last_name: str):
    """Dodaje nowego pracownika do bazy danych."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO employees (first_name, last_name) VALUES (?, ?)",
        (first_name, last_name)
    )
    conn.commit()
    conn.close()
