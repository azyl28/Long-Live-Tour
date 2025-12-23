-- =================================================================
-- Schema for the Fleet Management System
-- Version 2.0
--
-- This schema enforces strict data continuity and state management.
-- =================================================================

-- =================================================================
-- VEHICLES TABLE
-- Central point of reference for all vehicle data.
-- This table holds the CURRENT state of the vehicle.
-- =================================================================
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    registration_number TEXT NOT NULL UNIQUE,
    brand TEXT NOT NULL,
    model TEXT NOT NULL,
    vin TEXT UNIQUE,
    production_year INTEGER,
    fuel_type TEXT NOT NULL,
    tank_capacity REAL,
    -- Normative fuel consumption (l/100km)
    normative_consumption REAL NOT NULL,
    -- The single source of truth for the vehicle's current state
    current_mileage REAL NOT NULL DEFAULT 0,
    current_fuel REAL NOT NULL DEFAULT 0,
    -- available, in_trip, maintenance
    status TEXT NOT NULL DEFAULT 'available',
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =================================================================
-- DRIVERS TABLE
-- Manages driver information and qualifications.
-- =================================================================
CREATE TABLE IF NOT EXISTS drivers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    license_number TEXT NOT NULL UNIQUE,
    license_category TEXT NOT NULL,
    license_expiry DATE NOT NULL,
    phone_number TEXT,
    -- active, inactive
    status TEXT NOT NULL DEFAULT 'active'
);

-- =================================================================
-- KEYS TABLE
-- Manages the physical access to vehicles.
-- A key checkout is required to start a trip.
-- =================================================================
CREATE TABLE IF NOT EXISTS keys (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL UNIQUE,
    -- issued, returned
    status TEXT NOT NULL DEFAULT 'returned',
    current_driver_id INTEGER,
    checkout_time TIMESTAMP,
    issuer_name TEXT,
    return_time TIMESTAMP,
    returner_name TEXT,
    notes TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (current_driver_id) REFERENCES drivers(id) ON DELETE SET NULL
);

-- =================================================================
-- TRIPS TABLE (ROAD CARD)
-- Records every trip, inheriting the vehicle's state upon start.
-- =================================================================
CREATE TABLE IF NOT EXISTS trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    road_card_number TEXT UNIQUE,
    vehicle_id INTEGER NOT NULL,
    driver_id INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    -- Inherited from vehicles table at the moment of trip creation
    start_mileage REAL NOT NULL,
    start_fuel REAL NOT NULL,
    end_time TIMESTAMP,
    end_mileage REAL,
    end_fuel REAL,
    route TEXT NOT NULL,
    purpose TEXT,
    -- calculated fields upon trip completion
    distance REAL,
    fuel_consumed_calculated REAL,
    -- active, completed, cancelled
    status TEXT NOT NULL DEFAULT 'active',
    notes TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (driver_id) REFERENCES drivers(id) ON DELETE CASCADE
);

-- =================================================================
-- FUELING LOGS TABLE
-- The only way to increase a vehicle's fuel level.
-- =================================================================
CREATE TABLE IF NOT EXISTS fueling_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id INTEGER NOT NULL,
    trip_id INTEGER, -- Optional, if fueling happened during a trip
    fueling_time TIMESTAMP NOT NULL,
    mileage_at_fueling REAL NOT NULL,
    liters_added REAL NOT NULL,
    price_per_liter REAL,
    total_cost REAL,
    notes TEXT,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id) ON DELETE CASCADE,
    FOREIGN KEY (trip_id) REFERENCES trips(id) ON DELETE SET NULL
);

-- =================================================================
-- INDEXES FOR PERFORMANCE
-- =================================================================
CREATE INDEX IF NOT EXISTS idx_vehicles_status ON vehicles(status);
CREATE INDEX IF NOT EXISTS idx_drivers_status ON drivers(status);
CREATE INDEX IF NOT EXISTS idx_keys_status ON keys(status);
CREATE INDEX IF NOT EXISTS idx_trips_vehicle_id ON trips(vehicle_id);
CREATE INDEX IF NOT EXISTS idx_trips_driver_id ON trips(driver_id);
CREATE INDEX IF NOT EXISTS idx_trips_status ON trips(status);
CREATE INDEX IF NOT EXISTS idx_fueling_logs_vehicle_id ON fueling_logs(vehicle_id);
