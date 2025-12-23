import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.initialize_database import initialize_database

def main():
    """Główna funkcja uruchamiająca aplikację."""
    # Upewnij się, że baza danych jest zainicjalizowana
    initialize_database()

    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == '__main__':
    main()
