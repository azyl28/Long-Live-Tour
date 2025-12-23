import sys
import traceback

sys.path.append(".")

print("Testowanie modułów...\n")

try:
    from src.utils import helpers, constants

    print("✅ helpers.py załadowany")
    print("✅ constants.py załadowany")

    root = helpers.get_project_root()
    print(f"📁 Główny folder: {root}")

    print(f"⛽ Typy paliwa: {constants.FUEL_TYPES}")
    print(f"🚗 Statusy: {list(constants.VEHICLE_STATUS_DISPLAY.values())}")

    print("\n🎉 WSZYSTKIE TESTY PRZESZŁY POMYŚLNIE!")
except Exception as e:
    print(f"❌ BŁĄD: {e}")
    traceback.print_exc()

input("\nNaciśnij Enter...")
