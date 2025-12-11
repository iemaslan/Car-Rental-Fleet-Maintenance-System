import unittest
from domain.models import Vehicle, MaintenanceRecord
from services.maintenance_service import MaintenanceService

class TestMaintenanceService(unittest.TestCase):
    def setUp(self):
        self.maintenance_service = MaintenanceService()
        self.vehicle = Vehicle(id=1, vehicle_class="Economy", location="Branch A", status="Available", odometer=10000, fuel_level=0.8)

    def test_register_maintenance_plan(self):
        record = self.maintenance_service.register_maintenance_plan(
            vehicle=self.vehicle,
            service_type="Oil Change",
            odometer_threshold=15000,
            time_threshold="2025-12-01"
        )
        self.assertEqual(len(self.maintenance_service.maintenance_records), 1)
        self.assertEqual(record.service_type, "Oil Change")
        self.assertEqual(record.odometer_threshold, 15000)

    def test_list_due_vehicles(self):
        self.maintenance_service.register_maintenance_plan(
            vehicle=self.vehicle,
            service_type="Oil Change",
            odometer_threshold=15000,
            time_threshold="2025-12-01"
        )
        due_vehicles = self.maintenance_service.list_due_vehicles(current_odometer=14500, current_time="2025-11-15")
        self.assertEqual(len(due_vehicles), 1)
        self.assertEqual(due_vehicles[0].id, 1)

        due_vehicles = self.maintenance_service.list_due_vehicles(current_odometer=10000, current_time="2025-10-01")
        self.assertEqual(len(due_vehicles), 0)

if __name__ == "__main__":
    unittest.main()