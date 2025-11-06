import unittest
from domain.models import Customer, VehicleClass, Reservation
from services.reservation_service import ReservationService

class TestReservationService(unittest.TestCase):
    def setUp(self):
        self.reservation_service = ReservationService()
        self.customer = Customer(id=1, name="John Doe", email="john.doe@example.com", phone="1234567890")
        self.vehicle_class = VehicleClass(name="Economy", base_rate=50.0)

    def test_create_reservation(self):
        reservation = self.reservation_service.create_reservation(
            customer=self.customer,
            vehicle_class=self.vehicle_class,
            pickup_time="2025-11-01T10:00:00",
            return_time="2025-11-05T10:00:00",
            addons=["GPS", "ChildSeat"],
            insurance_tier="Standard",
            deposit=100.0
        )
        self.assertEqual(len(self.reservation_service.reservations), 1)
        self.assertEqual(reservation.customer.name, "John Doe")
        self.assertEqual(reservation.vehicle_class.name, "Economy")

    def test_modify_reservation(self):
        reservation = self.reservation_service.create_reservation(
            customer=self.customer,
            vehicle_class=self.vehicle_class,
            pickup_time="2025-11-01T10:00:00",
            return_time="2025-11-05T10:00:00",
            addons=["GPS"],
            insurance_tier="Standard",
            deposit=100.0
        )
        modified_reservation = self.reservation_service.modify_reservation(
            reservation_id=reservation.id,
            addons=["GPS", "ChildSeat"],
            deposit=150.0
        )
        self.assertIsNotNone(modified_reservation)
        self.assertEqual(modified_reservation.addons, ["GPS", "ChildSeat"])
        self.assertEqual(modified_reservation.deposit, 150.0)

    def test_cancel_reservation(self):
        reservation = self.reservation_service.create_reservation(
            customer=self.customer,
            vehicle_class=self.vehicle_class,
            pickup_time="2025-11-01T10:00:00",
            return_time="2025-11-05T10:00:00",
            addons=[],
            insurance_tier=None,
            deposit=100.0
        )
        result = self.reservation_service.cancel_reservation(reservation_id=reservation.id)
        self.assertTrue(result)
        self.assertEqual(len(self.reservation_service.reservations), 0)

if __name__ == "__main__":
    unittest.main()