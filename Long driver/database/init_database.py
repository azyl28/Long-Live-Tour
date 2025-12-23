"""
Database initialization
"""

import sqlite3
from pathlib import Path
import logging

class DatabaseInitializer:
    """Database initializer class"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        
    def initialize(self):
        """Initialize database"""
        try:
            # Create directory if not exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Connect to database (or create new)
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Load database schema
            schema_path = Path(__file__).parent / 'schema.sql'
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # Execute SQL script
            cursor.executescript(schema_sql)
            
            # Add sample data (for testing only)
            self.add_sample_data(cursor)
            
            # Commit and close
            conn.commit()
            conn.close()
            
            print(f"Database initialized: {self.db_path}")
            return True
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            raise
    
    def add_sample_data(self, cursor):
        """Add sample data to database (for testing)"""
        
        # Add sample employees
        employees = [
            (1, 'John', 'Doe', 'Driver', 'employee'),
            (2, 'Jane', 'Smith', 'Fleet Manager', 'manager'),
            (3, 'Robert', 'Johnson', 'Director', 'admin'),
            (4, 'Mary', 'Williams', 'Driver', 'employee'),
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO employees (id, first_name, last_name, position, permissions)
            VALUES (?, ?, ?, ?, ?)
        ''', employees)
        
        # Add sample vehicles
        vehicles = [
            (1, 'WA 12345', 'Toyota', 'Corolla', 'Gasoline', 6.5, 125430.5, 'available'),
            (2, 'KR 67890', 'Ford', 'Focus', 'Diesel', 5.8, 89210.2, 'available'),
            (3, 'GD 11223', 'Volkswagen', 'Transporter', 'Diesel', 8.2, 156780.0, 'service'),
            (4, 'PO 44556', 'Skoda', 'Octavia', 'LPG', 7.1, 65430.7, 'available'),
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO vehicles 
            (id, registration_number, brand, model, fuel_type, fuel_consumption, current_mileage, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', vehicles)
        
        print("Sample data added to database")

def main():
    """Main initialization function"""
    import sys
    
    # Database path
    db_path = "database/fleet.db"
    
    # Initialize database
    initializer = DatabaseInitializer(db_path)
    
    try:
        initializer.initialize()
        print(f"Database successfully initialized: {db_path}")
        print("Sample test data added.")
        print("\nAvailable test data:")
        print("  Employees: John Doe, Jane Smith, Robert Johnson, Mary Williams")
        print("  Vehicles: WA 12345 (Toyota), KR 67890 (Ford), GD 11223 (VW), PO 44556 (Skoda)")
    except Exception as e:
        print(f"Database initialization failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()