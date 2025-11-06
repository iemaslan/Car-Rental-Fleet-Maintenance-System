import unittest
from domain.models import Vehicle, VehicleClass
from services.inventory_service import InventoryService

class TestInventoryService(unittest.TestCase):
    def setUp(self):
        self.inventory_service = InventoryService()
        self.vehicle_class_economy = VehicleClass(name="Economy", base_rate=50.0)
        self.vehicle_class_suv = VehicleClass(name="SUV", base_rate=100.0)
        self.vehicle1 = Vehicle(id=1, vehicle_class="Economy", location="Branch A", status="Available", odometer=10000, fuel_level=0.8)
        self.vehicle2 = Vehicle(id=2, vehicle_class="SUV", location="Branch A", status="Available", odometer=20000, fuel_level=0.6)
        self.vehicle3 = Vehicle(id=3, vehicle_class="Economy", location="Branch B", status="Rented", odometer=15000, fuel_level=0.7)

    def test_add_vehicle(self):
        self.inventory_service.add_vehicle(self.vehicle1)
        self.assertEqual(len(self.inventory_service.vehicles), 1)
        self.assertEqual(self.inventory_service.vehicles[0].id, 1)

    def test_check_availability(self):
        self.inventory_service.add_vehicle(self.vehicle1)
        self.inventory_service.add_vehicle(self.vehicle2)
        self.inventory_service.add_vehicle(self.vehicle3)

        available_vehicles = self.inventory_service.check_availability(vehicle_class=self.vehicle_class_economy, location="Branch A", time_range=("2025-11-01", "2025-11-02"))
        self.assertEqual(len(available_vehicles), 1)
        self.assertEqual(available_vehicles[0].id, 1)

        available_vehicles = self.inventory_service.check_availability(vehicle_class=self.vehicle_class_suv, location="Branch A", time_range=("2025-11-01", "2025-11-02"))
        self.assertEqual(len(available_vehicles), 1)
        self.assertEqual(available_vehicles[0].id, 2)

if __name__ == "__main__":
    unittest.main()