import unittest
from domain.models import RentalAgreement, ChargeItem, Vehicle, VehicleClass, Reservation, Customer, AddOn, InsuranceTier
from services.pricing_policy import PricingPolicy, base_daily_rate_rule, addon_fee_rule, insurance_fee_rule

class TestPricingPolicy(unittest.TestCase):
    def setUp(self):
        self.pricing_policy = PricingPolicy()
        self.pricing_policy.add_pricing_rule(base_daily_rate_rule)
        self.pricing_policy.add_pricing_rule(addon_fee_rule)
        self.pricing_policy.add_pricing_rule(insurance_fee_rule)

        self.vehicle_class = VehicleClass(name="Economy", base_rate=50.0)
        self.vehicle = Vehicle(id=1, vehicle_class=self.vehicle_class, location="Branch A", status="Available", odometer=10000, fuel_level=0.8)
        self.customer = Customer(id=1, name="John Doe", email="john.doe@example.com", phone="1234567890")
        self.reservation = Reservation(
            id=1,
            customer=self.customer,
            vehicle_class=self.vehicle_class,
            pickup_time="2025-11-01T10:00:00",
            return_time="2025-11-05T10:00:00",
            addons=[AddOn(name="GPS", daily_fee=10.0), AddOn(name="ChildSeat", daily_fee=5.0)],
            insurance_tier=InsuranceTier(name="Standard", daily_fee=20.0),
            deposit=100.0
        )
        self.rental_agreement = RentalAgreement(
            id=1,
            reservation=self.reservation,
            vehicle=self.vehicle,
            start_odometer=10000,
            start_fuel_level=0.8
        )

    def test_base_daily_rate_rule(self):
        charges = base_daily_rate_rule(self.rental_agreement)
        self.assertEqual(len(charges), 1)
        self.assertEqual(charges[0].description, "Base Daily Rate")
        self.assertEqual(charges[0].amount, 50.0)  # Placeholder for 1 day calculation

    def test_addon_fee_rule(self):
        charges = addon_fee_rule(self.rental_agreement)
        self.assertEqual(len(charges), 1)
        self.assertEqual(charges[0].description, "Add-On Fees")
        self.assertEqual(charges[0].amount, 15.0)

    def test_insurance_fee_rule(self):
        charges = insurance_fee_rule(self.rental_agreement)
        self.assertEqual(len(charges), 1)
        self.assertEqual(charges[0].description, "Insurance Fee")
        self.assertEqual(charges[0].amount, 20.0)

    def test_calculate_charges(self):
        charges = self.pricing_policy.calculate_charges(self.rental_agreement)
        self.assertEqual(len(charges), 3)
        self.assertEqual(sum(charge.amount for charge in charges), 85.0)  # 50 + 15 + 20

if __name__ == "__main__":
    unittest.main()