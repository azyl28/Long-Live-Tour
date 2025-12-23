import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "fleet.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# USUŃ stare tabele
cursor.executescript("""
DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS keylog;
DROP TABLE IF EXISTS vehicles;
DROP TABLE IF EXISTS employees;
""")

# NOWY SCHEMAT Z CIĄGŁOŚCIĄ
cursor.executescript("""
-- Pojazdy (CENTRALNY STAN)
CREATE TABLE vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registrationnumber TEXT UNIQUE NOT NULL,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    fueltype TEXT,
    fuelconsumption REAL NOT NULL DEFAULT 7.5,
    tankcapacity REAL,
    currentmileage REAL NOT NULL DEFAULT 0,
    currentfuel REAL NOT NULL DEFAULT 0,
    status TEXT DEFAULT 'available',
    vin TEXT,
    productionyear INTEGER,
    notes TEXT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Pracownicy
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    phone TEXT,
    driving_license TEXT,
    license_expiry DATE,
    isactive INTEGER DEFAULT 1
);

-- Kluczyki (kontrola dostępu)
CREATE TABLE keylog (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicleid INTEGER,
    employeeid INTEGER,
    checkouttime DATETIME NOT NULL,
    checkoutmileage REAL,
    checkoutfuel REAL,
    issuer_employeeid INTEGER,
    returntime DATETIME,
    returnmileage REAL,
    returnfuel REAL,
    status TEXT DEFAULT 'out', -- out/returned
    notes TEXT,
    FOREIGN KEY(vehicleid) REFERENCES vehicles(id),
    FOREIGN KEY(employeeid) REFERENCES employees(id)
);

-- Przejazdy (ciągłość z pojazdem)
CREATE TABLE trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tripnumber TEXT,
    vehicleid INTEGER NOT NULL,
    employeeid INTEGER NOT NULL,
    keylogid INTEGER,
    startdate DATETIME NOT NULL,
    startmileage REAL NOT NULL, -- Zawsze = currentmileage pojazdu
    startfuel REAL NOT NULL,    -- Zawsze = currentfuel pojazdu
    purpose TEXT,
    orderedby TEXT,
    enddate DATETIME,
    endmileage REAL,
    endfuel REAL,
    distance REAL GENERATED ALWAYS AS (endmileage - startmileage) STORED,
    fuelused REAL,
    calculatedfuel REAL,
    fuelcost REAL,
    vehicleok INTEGER DEFAULT 1,
    notes TEXT,
    status TEXT DEFAULT 'active', -- active/completed
    FOREIGN KEY(vehicleid) REFERENCES vehicles(id),
    FOREIGN KEY(employeeid) REFERENCES employees(id),
    FOREIGN KEY(keylogid) REFERENCES keylog(id)
);

-- Indeksy dla wydajności
CREATE INDEX idx_vehicles_reg ON vehicles(registrationnumber);
CREATE INDEX idx_trips_vehicle_status ON trips(vehicleid, status);
CREATE INDEX idx_trips_employee ON trips(employeeid);
CREATE INDEX idx_keylog_vehicle_status ON keylog(vehicleid, status);
CREATE INDEX idx_trips_dates ON trips(startdate, enddate);

-- DANE TESTOWE
INSERT OR IGNORE INTO vehicles (registrationnumber, brand, model, fuelconsumption, currentmileage, currentfuel, status) 
VALUES ('WX12345', 'Ford', 'Transit', 8.5, 15000, 55.0, 'available');

INSERT OR IGNORE INTO employees (firstname, lastname, isactive) VALUES ('Jan', 'Kowalski', 1);

PRINT '✅ Schemat utworzony z danymi testowymi';
""")

conn.commit()
conn.close()
print("✅ Baza gotowa!")
