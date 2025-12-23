"""
Stałe aplikacji - centralne miejsce na wszystkie stałe wartości
"""

# ============================================================================
# STATUSY POJAZDÓW
# ============================================================================
VEHICLE_STATUS = {
    'AVAILABLE': 'w_firmie',
    'IN_TRANSIT': 'w_trasie',
    'IN_SERVICE': 'serwis',
    'BROKEN': 'awaria'
}

VEHICLE_STATUS_DISPLAY = {
    'w_firmie': 'Dostępny',
    'w_trasie': 'W trasie',
    'serwis': 'W serwisie',
    'awaria': 'Awaria'
}

# ============================================================================
# TYPY PALIWA
# ============================================================================
FUEL_TYPES = [
    'Benzyna',
    'Diesel',
    'LPG',
    'Hybryda',
    'Elektryk'
]

# Domyślne ceny paliwa [PLN/l] - można nadpisać w config.yaml
DEFAULT_FUEL_PRICES = {
    'Benzyna': 6.50,
    'Diesel': 6.20,
    'LPG': 3.00,
    'Hybryda': 6.50,  # domyślnie jak benzyna
    'Elektryk': 0.0   # do obliczeń
}

# ============================================================================
# UPRAWNIENIA PRACOWNIKÓW
# ============================================================================
PERMISSION_LEVELS = {
    'EMPLOYEE': 'pracownik',
    'MANAGER': 'kierownik',
    'ADMIN': 'administrator'
}

PERMISSION_DISPLAY = {
    'pracownik': 'Pracownik',
    'kierownik': 'Kierownik',
    'administrator': 'Administrator'
}

# ============================================================================
# RODZAJE ZLECEŃ/WYJAZDÓW
# ============================================================================
ASSIGNMENT_TYPES = [
    'Prezes',
    'Dyrektor',
    'Klient',
    'Serwis',
    'Inne'
]

# ============================================================================
# STATUSY KARTY DROGOWEJ
# ============================================================================
TRIP_SHEET_STATUS = {
    'OPEN': 'otwarta',
    'CLOSED': 'zamknięta',
    'ARCHIVED': 'archiwum'
}

TRIP_SHEET_STATUS_DISPLAY = {
    'otwarta': 'Otwarta',
    'zamknięta': 'Zamknięta',
    'archiwum': 'Archiwum'
}

# ============================================================================
# ŚCIEŻKI DO FOLDERÓW
# ============================================================================
DIRECTORIES = {
    'DATABASE': 'database/',
    'REPORTS_PDF': 'reports/pdf/',
    'REPORTS_CSV': 'reports/csv/',
    'BACKUP': 'backup/',
    'SIGNATURES': 'signatures/',
    'TEMPLATES': 'src/templates/'
}

# ============================================================================
# USTAWIENIA PDF (dla ReportLab)
# ============================================================================
PDF_SETTINGS = {
    'PAGE_SIZE': 'A4',
    'MARGIN_MM': 20,
    'FONT_NAME': 'Helvetica',
    'FONT_SIZE_NORMAL': 10,
    'FONT_SIZE_HEADER': 14,
    'FONT_SIZE_TITLE': 18
}

# ============================================================================
# KOLORY APLIKACJI (dla GUI)
# ============================================================================
APP_COLORS = {
    # Kolory podstawowe
    'PRIMARY': '#3498db',      # Niebieski
    'SECONDARY': '#2c3e50',    # Ciemny granat
    'SUCCESS': '#27ae60',      # Zielony
    'WARNING': '#f39c12',      # Pomarańczowy
    'DANGER': '#e74c3c',       # Czerwony
    
    # Kolory tła
    'BACKGROUND_LIGHT': '#ecf0f1',
    'BACKGROUND_DARK': '#34495e',
    
    # Kolory tekstu
    'TEXT_LIGHT': '#ffffff',
    'TEXT_DARK': '#2c3e50',
    'TEXT_MUTED': '#7f8c8d',
    
    # Kolory statusów
    'STATUS_AVAILABLE': '#27ae60',     # Zielony
    'STATUS_IN_TRANSIT': '#f39c12',    # Pomarańczowy
    'STATUS_SERVICE': '#e74c3c',       # Czerwony
    'STATUS_BROKEN': '#95a5a6',        # Szary
}

# ============================================================================
# OGRANICZENIA BIZNESOWE
# ============================================================================
BUSINESS_RULES = {
    'MAX_MILEAGE_CORRECTION_KM': 50,      # Maksymalna korekta przebiegu
    'MIN_TRIP_DISTANCE_KM': 0.1,          # Minimalny dystans przejazdu
    'MAX_FUEL_CONSUMPTION': 30.0,         # Maksymalne spalanie [l/100km]
    'MIN_EMPLOYEE_AGE': 18,               # Minimalny wiek pracownika
    'MAX_HOURS_PER_DAY': 12,              # Maksymalna liczba godzin pracy dziennie
}

# ============================================================================
# FORMATY DATY I CZASU
# ============================================================================
DATE_FORMATS = {
    'DISPLAY': '%d.%m.%Y',           # 15.01.2024
    'DATABASE': '%Y-%m-%d',          # 2024-01-15
    'FULL': '%A, %d %B %Y',          # Poniedziałek, 15 stycznia 2024
}

TIME_FORMATS = {
    'DISPLAY': '%H:%M',              # 14:30
    'DATABASE': '%H:%M:%S',          # 14:30:00
    'FULL': '%H:%M:%S',              # 14:30:00
}

DATETIME_FORMATS = {
    'DISPLAY': '%d.%m.%Y %H:%M',     # 15.01.2024 14:30
    'DATABASE': '%Y-%m-%d %H:%M:%S', # 2024-01-15 14:30:00
    'FILE': '%Y%m%d_%H%M%S',         # 20240115_143000
}

# ============================================================================
# WIADOMOŚCI I TEKSTY
# ============================================================================
MESSAGES = {
    # Błędy walidacji
    'ERROR_MILEAGE_BACKWARDS': 'Przebieg końcowy nie może być mniejszy od początkowego!',
    'ERROR_VEHICLE_UNAVAILABLE': 'Pojazd jest niedostępny. Sprawdź status.',
    'ERROR_EMPLOYEE_INACTIVE': 'Pracownik jest nieaktywny.',
    'ERROR_INVALID_DATE': 'Nieprawidłowa data.',
    'ERROR_INVALID_TIME': 'Nieprawidłowa godzina.',
    
    # Potwierdzenia
    'CONFIRM_DELETE': 'Czy na pewno chcesz usunąć ten element?',
    'CONFIRM_CHECKOUT': 'Czy potwierdzasz pobranie pojazdu?',
    'CONFIRM_RETURN': 'Czy potwierdzasz zwrot pojazdu?',
    
    # Sukcesy
    'SUCCESS_SAVE': 'Dane zostały zapisane pomyślnie.',
    'SUCCESS_DELETE': 'Element został usunięty.',
    'SUCCESS_CHECKOUT': 'Pobranie pojazdu zarejestrowane.',
    'SUCCESS_RETURN': 'Zwrot pojazdu zarejestrowany.',
    
    # Informacje
    'INFO_NO_DATA': 'Brak danych do wyświetlenia.',
    'INFO_SELECT_ITEM': 'Wybierz element z listy.',
}

# ============================================================================
# USTAWIENIA BAZY DANYCH
# ============================================================================
DATABASE = {
    'NAME': 'fleet.db',
    'TIMEOUT': 5.0,           # Sekundy
    'DETECT_TYPES': True,
    'ISOLATION_LEVEL': None,  # Autocommit mode
}

# ============================================================================
# OGRANICZENIA INTERFEJSU
# ============================================================================
UI_LIMITS = {
    'MAX_RECORDS_PER_PAGE': 100,
    'AUTO_REFRESH_SECONDS': 30,
    'MAX_FILE_SIZE_MB': 10,    # Maksymalny rozmiar załączanego pliku
}

# ============================================================================
# NUMERACJA KART DROGOWYCH
# ============================================================================
TRIP_SHEET_NUMBERING = {
    'PREFIX': 'KD',
    'SEPARATOR': '/',
    'YEAR_DIGITS': 4,
    'SEQUENCE_DIGITS': 4,
}

if __name__ == "__main__":
    # Prosty test czy moduł się ładuje
    print("=" * 50)
    print("STAŁE APLIKACJI - SYSTEM EWIDENCJI POJAZDÓW")
    print("=" * 50)
    print(f"✅ Zdefiniowanych typów paliwa: {len(FUEL_TYPES)}")
    print(f"✅ Statusy pojazdów: {len(VEHICLE_STATUS)}")
    print(f"✅ Kolory aplikacji: {len(APP_COLORS)}")
    print(f"✅ Domyślne formaty daty: {len(DATE_FORMATS)}")
    print("=" * 50)
    print("Moduł constants.py załadowany pomyślnie.")