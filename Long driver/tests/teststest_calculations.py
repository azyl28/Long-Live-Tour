# tests/test_calculations.py
import unittest
from src.models.vehicle import Vehicle
from src.services.trip_calculator import TripCalculator

class TestCalculations(unittest.TestCase):
    
    def test_fuel_calculation(self):
        """Test obliczania zużycia paliwa"""
        vehicle = Vehicle(
            fuel_consumption=7.5,  # 7.5l/100km
            current_mileage=100000
        )
        
        # Dla 150 km
        fuel_used = vehicle.calculate_fuel_usage(150)
        self.assertAlmostEqual(fuel_used, 11.25)  # 150/100 * 7.5 = 11.25
        
    def test_mileage_validation(self):
        """Test walidacji przebiegu"""
        vehicle = Vehicle(current_mileage=100000)
        
        # Nowy przebieg nie może być mniejszy
        with self.assertRaises(ValueError):
            vehicle.update_mileage(99999, 1, "test")
            
        # Poprawna aktualizacja
        result = vehicle.update_mileage(100150, 1, "zwrot")
        self.assertEqual(result['new_mileage'], 100150)
        self.assertEqual(vehicle.current_mileage, 100150)

if __name__ == '__main__':
    unittest.main()