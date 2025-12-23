-- Tabela pojazdów
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    registration_number TEXT NOT NULL UNIQUE,
    status TEXT NOT NULL CHECK(status IN ('W_FIRMIE', 'W_TRASIE', 'SERWIS')),
    mileage REAL NOT NULL,
    fuel_consumption REAL NOT NULL -- Spalanie na 100 km
);

-- Tabela pracowników
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL
);

-- Tabela kart drogowych
CREATE TABLE IF NOT EXISTS road_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('OTWARTA', 'ZAMKNIETA')),
    start_mileage REAL NOT NULL,
    end_mileage REAL,
    start_date TEXT NOT NULL,
    end_date TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles (id),
    FOREIGN KEY (employee_id) REFERENCES employees (id)
);

-- Tabela ewidencji pobrania/zwrotu kluczy (log)
CREATE TABLE IF NOT EXISTS keys_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    road_card_id INTEGER NOT NULL,
    action TEXT NOT NULL CHECK(action IN ('POBRANIE', 'ZWROT')),
    timestamp TEXT NOT NULL,
    FOREIGN KEY (road_card_id) REFERENCES road_cards (id)
);

-- Tabela przejazdów
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    road_card_id INTEGER NOT NULL,
    origin TEXT NOT NULL,
    destination TEXT NOT NULL,
    purpose TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    FOREIGN KEY (road_card_id) REFERENCES road_cards (id)
);
