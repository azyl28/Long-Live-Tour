-- =========================================
-- ZAKTUALIZOWANY SCHEMAT BAZY DANYCH
-- =========================================

-- Tabela pracowników (bez zmian)
-- =========================================
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    position TEXT,
    department TEXT, -- dział / komórka
    permissions TEXT DEFAULT 'employee',
    email TEXT,
    phone TEXT,
    is_active INTEGER DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================================
-- Tabela pojazdów - DODANE current_fuel
-- =========================================
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_number TEXT NOT NULL UNIQUE,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    fuel_type TEXT NOT NULL,
    fuel_consumption REAL NOT NULL DEFAULT 7.5, -- l/100km (średnie spalanie katalogowe)
    current_mileage REAL DEFAULT 0,
    current_fuel REAL DEFAULT 50, -- AKUALNY STAN PALIWA (NOWE POLE)
    status TEXT DEFAULT 'available', -- available, inuse, service, broken
    tank_capacity REAL,
    vin TEXT, -- numer VIN
    production_year INTEGER, -- rok produkcji
    notes TEXT, -- uwagi o pojeździe
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (id) REFERENCES key_log(vehicle_id) ON DELETE CASCADE
);

-- =========================================
-- Tabela dziennika kluczy (bez zmian)
-- =========================================
CREATE TABLE IF NOT EXISTS key_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL, -- pojazd
    employee_id INTEGER NOT NULL, -- kto bierze klucz
    checkout_time TIMESTAMP NOT NULL, -- data/godzina wydania
    return_time TIMESTAMP, -- data/godzina zwrotu (NULL = jeszcze w trasie)
    checkout_mileage REAL, -- przebieg przy wydaniu
    return_mileage REAL, -- przebieg przy zwrocie
    checkout_fuel REAL, -- paliwo przy wydaniu (L)
    return_fuel REAL, -- paliwo przy zwrocie
    storage_location TEXT, -- gdzie są klucze (np. Szafka A3)
    status TEXT DEFAULT 'out', -- out / returned
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE
);

-- Indeksy dla key_log
CREATE INDEX IF NOT EXISTS idx_keylog_vehicle ON key_log(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_keylog_employee ON key_log(employee_id);
CREATE INDEX IF NOT EXISTS idx_keylog_status ON key_log(status);

-- =========================================
-- Tabela przejazdów - UZUPEŁNIONE fuel_used, calculated_consumption
-- =========================================
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    -- Podstawowe informacje
    trip_number TEXT UNIQUE, -- Numer karty drogowej (opcjonalnie)
    vehicle_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    key_log_id INTEGER, -- wpis w key_log, z którego startuje przejazd
    
    -- Daty i miejsca
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP,
    start_location TEXT,
    end_location TEXT,
    destination TEXT, -- Cel podróży
    purpose TEXT, -- Opis / cel służbowy
    ordered_by TEXT, -- Kto zlecił wyjazd
    
    -- Przebieg
    start_mileage REAL,
    end_mileage REAL,
    distance REAL, -- Dystans tego przejazdu (km)
    
    -- Paliwo - ROZSZERZONE
    start_fuel REAL, -- Stan paliwa na wyjeździe (L)
    end_fuel REAL, -- Stan paliwa po powrocie (L)
    fuel_used REAL, -- Rzeczywiste zużyte paliwo (L)
    calculated_fuel REAL, -- PRZELICZONE zużycie wg średniego spalania (L)
    
    fuel_cost REAL, -- Koszt paliwa
    fuel_type TEXT, -- Rodzaj paliwa
    avg_consumption REAL, -- Średnie spalanie z vehicles (L/100km)
    
    -- Status i uwagi
    status TEXT DEFAULT 'active', -- active / completed / cancelled
    vehicle_ok INTEGER DEFAULT 1, -- Czy pojazd sprawny (checkbox)
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Klucze obce
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
    FOREIGN KEY (key_log_id) REFERENCES key_log(id) ON DELETE SET NULL
);

-- Indeksy dla trips
CREATE INDEX IF NOT EXISTS idx_trips_dates ON trips(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_trips_status ON trips(status);
CREATE INDEX IF NOT EXISTS idx_trips_vehicle ON trips(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_trips_employee ON trips(employee_id);
CREATE INDEX IF NOT EXISTS idx_trips_number ON trips(trip_number);

-- =========================================
-- SKRYPTY MIGRACJI - DODAJE NOWE KOLUMNY
-- =========================================
-- DODAJ current_fuel DO vehicles (jeśli nie istnieje)
ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS current_fuel REAL DEFAULT 50;

-- DODAJ calculated_fuel DO trips (jeśli nie istnieje)
ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS fuel_consumption REAL DEFAULT 7.5;

-- Ustaw domyślne wartości dla istniejących pojazdów
UPDATE vehicles SET current_fuel = 50 WHERE current_fuel IS NULL;
UPDATE vehicles SET fuel_consumption = 7.5 WHERE fuel_consumption IS NULL;

-- =========================================
-- WYŚWIETL STRUKTURĘ PO ZMIANACH
-- =========================================
-- .schema vehicles
-- .schema trips
-- .schema key_log
