import unittest
from domain.models import Customer, Vehicle, VehicleClass, Reservation, RentalAgreement
from services.rental_service import RentalService

class TestRentalService(unittest.TestCase):
    def setUp(self):
        self.rental_service = RentalService()
        self.vehicle_class = VehicleClass(name="Economy", base_rate=50.0)
        self.vehicle = Vehicle(id=1, vehicle_class="Economy", location="Branch A", status="Available", odometer=10000, fuel_level=0.8)
        self.customer = Customer(id=1, name="John Doe", email="john.doe@example.com", phone="1234567890")
        self.reservation = Reservation(
            id=1,
            customer=self.customer,
            vehicle_class=self.vehicle_class,
            pickup_time="2025-11-01T10:00:00",
            return_time="2025-11-05T10:00:00",
            addons=[],
            insurance_tier=None,
            deposit=100.0
        )

    def test_pickup_vehicle(self):
        rental_agreement = self.rental_service.pickup_vehicle(
            reservation=self.reservation,
            vehicle=self.vehicle,
            start_odometer=10000,
            start_fuel_level=0.8
        )
        self.assertIsNotNone(rental_agreement)
        self.assertEqual(rental_agreement.vehicle.id, 1)
        self.assertEqual(rental_agreement.start_odometer, 10000)
        self.assertEqual(self.vehicle.status, "Rented")

    def test_return_vehicle(self):
        rental_agreement = self.rental_service.pickup_vehicle(
            reservation=self.reservation,
            vehicle=self.vehicle,
            start_odometer=10000,
            start_fuel_level=0.8
        )
        invoice = self.rental_service.return_vehicle(
            rental_agreement_id=rental_agreement.id,
            end_odometer=10200,
            end_fuel_level=0.5
        )
        self.assertIsNotNone(invoice)
        self.assertEqual(invoice.total_amount, 150.0)  # Placeholder logic for charges
        self.assertEqual(self.vehicle.status, "Available")

    def test_extend_rental(self):
        rental_agreement = self.rental_service.pickup_vehicle(
            reservation=self.reservation,
            vehicle=self.vehicle,
            start_odometer=10000,
            start_fuel_level=0.8
        )
        result = self.rental_service.extend_rental(
            rental_agreement_id=rental_agreement.id,
            new_return_time="2025-11-07T10:00:00"
        )
        self.assertTrue(result)
        self.assertEqual(rental_agreement.reservation.return_time, "2025-11-07T10:00:00")

if __name__ == "__main__":
    unittest.main()