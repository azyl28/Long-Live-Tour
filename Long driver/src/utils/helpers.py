"""
Pomocnicze funkcje dla aplikacji
"""
import os
import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, Any

def setup_logging():
    """Konfiguruje system logowania"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('app.log', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def setup_directories():
    """
    Tworzy wszystkie wymagane foldery aplikacji.
    """
    required_dirs = [
        'database',
        'reports/pdf',
        'reports/csv',
        'backup',
        'signatures',
        'src/gui/components',
        'src/templates'
    ]
    
    logger = logging.getLogger(__name__)
    
    for dir_path in required_dirs:
        path = Path(dir_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Utworzono/sprawdzono folder: {dir_path}")
        except Exception as e:
            logger.error(f"Błąd tworzenia folderu {dir_path}: {e}")
            raise
    
    logger.info("Wszystkie foldery aplikacji są gotowe.")

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """
    Ładuje konfigurację z pliku YAML.
    
    Args:
        config_path: Ścieżka do pliku konfiguracyjnego
        
    Returns:
        Słownik z konfiguracją lub domyślne ustawienia
    """
    logger = logging.getLogger(__name__)
    
    # Domyślna konfiguracja
    default_config = {
        'app': {
            'name': 'System Ewidencji Pojazdów',
            'version': '1.0.0',
            'company': 'Twoja Firma Sp. z o.o.',
            'language': 'pl'
        },
        'database': {
            'path': 'database/fleet.db',
            'backup_path': 'backup/',
            'backup_interval_hours': 24,
            'max_backup_files': 30
        },
        'pdf': {
            'output_path': 'reports/pdf/',
            'default_font': 'Helvetica',
            'font_size': 10
        },
        'ui': {
            'theme': 'light',
            'font_size': 12
        }
    }
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        logger.warning(f"Plik konfiguracyjny {config_path} nie istnieje. Używam domyślnych ustawień.")
        return default_config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            user_config = yaml.safe_load(f) or {}
        
        # Połączenie domyślnej i użytkowniczej konfiguracji
        merged_config = default_config.copy()
        
        # Rekurencyjne mergowanie słowników
        def merge_dicts(default, user):
            for key, value in user.items():
                if key in default and isinstance(default[key], dict) and isinstance(value, dict):
                    merge_dicts(default[key], value)
                else:
                    default[key] = value
        
        merge_dicts(merged_config, user_config)
        
        logger.info(f"Załadowano konfigurację z {config_path}")
        return merged_config
        
    except yaml.YAMLError as e:
        logger.error(f"Błąd parsowania YAML w {config_path}: {e}")
        return default_config
    except Exception as e:
        logger.error(f"Błąd ładowania konfiguracji {config_path}: {e}")
        return default_config

def get_project_root() -> Path:
    """
    Zwraca ścieżkę do głównego folderu projektu.
    
    Returns:
        Path: Ścieżka do katalogu głównego
    """
    # Zakładamy, że helpers.py jest w src/utils/
    # Więc rodzic rodzica to główny folder projektu
    return Path(__file__).parent.parent.parent

def validate_file_path(file_path: str, check_exists: bool = True) -> bool:
    """
    Sprawdza poprawność ścieżki do pliku.
    
    Args:
        file_path: Ścieżka do sprawdzenia
        check_exists: Czy sprawdzać istnienie pliku
        
    Returns:
        bool: True jeśli ścieżka jest poprawna
    """
    try:
        path = Path(file_path)
        
        # Sprawdź czy ścieżka jest bezwzględna
        if not path.is_absolute():
            # Konwertuj na ścieżkę względem głównego folderu projektu
            project_root = get_project_root()
            path = project_root / path
        
        # Sprawdź czy folder rodzica istnieje
        if not path.parent.exists():
            return False
        
        # Sprawdź czy plik istnieje (jeśli wymagane)
        if check_exists and not path.exists():
            return False
            
        return True
        
    except Exception:
        return False

def format_currency(amount: float) -> str:
    """
    Formatuje kwotę jako walutę PLN.
    
    Args:
        amount: Kwota do sformatowania
        
    Returns:
        str: Sformatowana kwota z symbolem PLN
    """
    return f"{amount:,.2f} PLN".replace(',', ' ').replace('.', ',')

def format_distance(distance_km: float) -> str:
    """
    Formatuje dystans w kilometrach.
    
    Args:
        distance_km: Dystans w kilometrach
        
    Returns:
        str: Sformatowany dystans
    """
    if distance_km >= 1000:
        return f"{distance_km/1000:,.1f} tys. km".replace(',', ' ')
    return f"{distance_km:,.1f} km".replace(',', ' ')

def safe_float_conversion(value: Any, default: float = 0.0) -> float:
    """
    Bezpiecznie konwertuje wartość na float.
    
    Args:
        value: Wartość do konwersji
        default: Wartość domyślna jeśli konwersja się nie uda
        
    Returns:
        float: Skonwertowana wartość
    """
    if value is None:
        return default
    
    try:
        # Spróbuj zamienić przecinki na kropki (format polski)
        if isinstance(value, str):
            value = value.replace(',', '.')
        
        return float(value)
    except (ValueError, TypeError):
        return default

def create_backup():
    """
    Tworzy kopię zapasową ważnych plików.
    """
    import shutil
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    backup_dir = Path("backup")
    backup_dir.mkdir(exist_ok=True)
    
    files_to_backup = [
        Path("database/fleet.db"),
        Path("config.yaml")
    ]
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for file_path in files_to_backup:
        if file_path.exists():
            backup_file = backup_dir / f"{file_path.name}.backup_{timestamp}"
            try:
                shutil.copy2(file_path, backup_file)
                logger.info(f"Utworzono kopię: {backup_file}")
            except Exception as e:
                logger.error(f"Błąd kopiowania {file_path}: {e}")

def resource_path(relative_path: str) -> Path:
    """
    Zwraca pełną ścieżkę do zasobu (dla PyInstaller).
    
    Args:
        relative_path: Względna ścieżka do zasobu
        
    Returns:
        Path: Pełna ścieżka do zasobu
    """
    if hasattr(sys, '_MEIPASS'):
        # Jesteśmy wewnątrz pliku wykonywalnego PyInstaller
        base_path = Path(sys._MEIPASS)
    else:
        # Jesteśmy w środowisku developerskim
        base_path = get_project_root()
    
    return base_path / relative_path

if __name__ == "__main__":
    # Testowanie funkcji
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Testowanie modułu helpers.py...")
    logger.info(f"Główny folder projektu: {get_project_root()}")
    
    config = load_config()
    logger.info(f"Załadowana konfiguracja: {config['app']['name']} v{config['app']['version']}")
    
    print("✅ Moduł helpers.py działa poprawnie")