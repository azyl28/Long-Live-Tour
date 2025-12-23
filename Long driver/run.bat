@echo off
chcp 65001 > nul
cls
echo ========================================
echo   System Ewidencji Pojazdow - Long Driver
echo ========================================
echo.

cd /d "%~dp0"

REM Sprawdz czy Python jest zainstalowany
python --version > nul 2>&1
if errorlevel 1 (
    echo BLAD: Python nie jest zainstalowany!
    pause
    exit /b 1
)

REM Sprawdz czy baza danych istnieje
if not exist "database\fleet.db" (
    echo INFO: Tworze baze danych...
    python database\init_database.py
)

echo.
echo INFO: Uruchamiam aplikacje...
echo.

python main.py

echo.
pause