"""
Comprehensive test for the updated CRFMS system.
Tests value objects, clock, pricing, and full rental workflow.
"""
import unittest
from decimal import Decimal
from datetime import datetime, timedelta

# Import from CRFMS package
from CRFMS.domain.value_objects import Money, FuelLevel, Kilometers
from CRFMS.domain.clock import SystemClock, FixedClock
from CRFMS.domain.models import (
    Customer, VehicleClass, Vehicle, VehicleStatus, Location,
    AddOn, InsuranceTier, Reservation, RentalAgreement
)

# Import from services
from CRFMS.services.maintenance_service import MaintenanceService
from CRFMS.services.pricing_policy import (
    PricingPolicy, BaseRateRule, AddOnRule, InsuranceRule,
    LateFeeRule, MileageOverageRule, FuelRefillRule,
    create_standard_pricing_policy
)
from CRFMS.services.rental_service import RentalService
from CRFMS.services.inventory_service import InventoryService
from CRFMS.services.reservation_service import ReservationService
from CRFMS.services.accounting_service import AccountingService

# Import from adapters
from CRFMS.adapters.notification_port import InMemoryNotificationAdapter
from CRFMS.adapters.payment_port import FakePaymentAdapter


class TestValueObjects(unittest.TestCase):
    """Test value objects."""
    
    def test_money_arithmetic(self):
        """Test Money arithmetic operations."""
        m1 = Money(Decimal('100.00'))
        m2 = Money(Decimal('50.00'))
        
        self.assertEqual(m1 + m2, Money(Decimal('150.00')))
        self.assertEqual(m1 - m2, Money(Decimal('50.00')))
        self.assertEqual(m1 * 2, Money(Decimal('200.00')))
        self.assertTrue(m1 > m2)
    
    def test_fuel_level_validation(self):
        """Test FuelLevel validation."""
        f1 = FuelLevel(0.8)
        self.assertEqual(f1.level, 0.8)
        
        with self.assertRaises(ValueError):
            FuelLevel(1.5)  # Invalid: > 1.0
        
        with self.assertRaises(ValueError):
            FuelLevel(-0.1)  # Invalid: < 0.0
    
    def test_kilometers_arithmetic(self):
        """Test Kilometers arithmetic."""
        k1 = Kilometers(1000)
        k2 = Kilometers(500)
        
        self.assertEqual(k1 + k2, Kilometers(1500))
        self.assertEqual(k1 - k2, Kilometers(500))
        self.assertTrue(k1 > k2)


class TestClock(unittest.TestCase):
    """Test clock implementations."""
    
    def test_fixed_clock(self):
        """Test FixedClock for deterministic testing."""
        fixed_time = datetime(2025, 10, 31, 10, 0, 0)
        clock = FixedClock(fixed_time)
        
        self.assertEqual(clock.now(), fixed_time)
        
        # Advance by 1 hour
        clock.advance(hours=1)
        self.assertEqual(clock.now(), datetime(2025, 10, 31, 11, 0, 0))


class TestPricingPolicy(unittest.TestCase):
    """Test pricing policy and rules."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.clock = FixedClock(datetime(2025, 10, 31, 10, 0, 0))
        
        # Create vehicle and reservation
        self.vehicle_class = VehicleClass("Economy", Money(Decimal('50.00')), 200)
        self.location = Location(1, "Branch A", "123 Main St")
        self.vehicle = Vehicle(
            1, self.vehicle_class, self.location, VehicleStatus.AVAILABLE,
            Kilometers(10000), FuelLevel(0.8)
        )
        
        self.customer = Customer(1, "John Doe", "john@example.com", "555-1234")
        
        pickup_time = self.clock.now()
        return_time = pickup_time + timedelta(days=3)
        
        self.reservation = Reservation(
            1, self.customer, self.vehicle_class, self.location,
            pickup_time, return_time, [], None, Money.zero()
        )
        
        self.rental = RentalAgreement(
            1, self.reservation, self.vehicle, "token123",
            Kilometers(10000), FuelLevel(0.8),
            pickup_time, return_time
        )
    
    def test_base_rate_calculation(self):
        """Test base rate rule."""
        policy = PricingPolicy(self.clock)
        policy.add_rule(BaseRateRule())
        
        charges = policy.calculate_charges(self.rental)
        
        self.assertEqual(len(charges), 1)
        # 3 days * $50/day = $150
        self.assertEqual(charges[0].amount, Money(Decimal('150.00')))
    
    def test_late_fee_calculation(self):
        """Test late fee with grace period."""
        # Create rental with actual return time set
        pickup_time = self.clock.now()
        expected_return = pickup_time + timedelta(days=3)
        
        # Set actual return time 3 hours late
        actual_return = expected_return + timedelta(hours=3)
        
        # Update rental with actual return info
        self.rental.actual_return_time = actual_return
        self.rental.expected_return_time = expected_return
        
        policy = PricingPolicy(self.clock)
        late_fee_rate = Money(Decimal('25.00'))
        policy.add_rule(LateFeeRule(late_fee_rate, grace_period_hours=1))
        
        charges = policy.calculate_charges(self.rental)
        
        # 3 hours late - 1 hour grace = 2 hours * $25 = $50
        self.assertEqual(len(charges), 1)
        self.assertEqual(charges[0].amount, Money(Decimal('50.00')))
    
    def test_mileage_overage_calculation(self):
        """Test mileage overage charges."""
        # Drive 800 km (allowance is 200 km/day * 3 days = 600 km)
        self.rental.end_odometer = Kilometers(10800)
        
        policy = PricingPolicy(self.clock)
        overage_rate = Money(Decimal('0.50'))
        policy.add_rule(MileageOverageRule(overage_rate))
        
        charges = policy.calculate_charges(self.rental)
        
        # 800 - 600 = 200 km overage * $0.50 = $100
        self.assertEqual(len(charges), 1)
        self.assertEqual(charges[0].amount, Money(Decimal('100.00')))


class TestRentalWorkflow(unittest.TestCase):
    """Test complete rental workflow."""
    
    def setUp(self):
        """Set up test services."""
        self.clock = FixedClock(datetime(2025, 10, 31, 10, 0, 0))
        self.notification_port = InMemoryNotificationAdapter(self.clock)
        self.payment_port = FakePaymentAdapter(self.clock, simulate_failure=False)
        
        self.maintenance_service = MaintenanceService(self.clock)
        self.pricing_policy = create_standard_pricing_policy(self.clock)
        self.rental_service = RentalService(
            self.clock, self.pricing_policy, self.maintenance_service
        )
        self.reservation_service = ReservationService(self.clock, self.notification_port)
        self.accounting_service = AccountingService(
            self.clock, self.payment_port, self.notification_port
        )
        self.inventory_service = InventoryService(self.clock, self.maintenance_service)
        
        # Create test data
        self.vehicle_class = VehicleClass("Economy", Money(Decimal('50.00')), 200)
        self.location = Location(1, "Branch A", "123 Main St")
        self.vehicle = Vehicle(
            1, self.vehicle_class, self.location, VehicleStatus.AVAILABLE,
            Kilometers(10000), FuelLevel(0.8)
        )
        self.inventory_service.add_vehicle(self.vehicle)
        
        self.customer = Customer(1, "John Doe", "john@example.com", "555-1234")
    
    def test_complete_rental_flow(self):
        """Test complete rental flow from reservation to payment."""
        # 1. Create reservation
        pickup_time = self.clock.now() + timedelta(days=1)
        return_time = pickup_time + timedelta(days=3)
        
        reservation = self.reservation_service.create_reservation(
            self.customer, self.vehicle_class, self.location,
            pickup_time, return_time
        )
        
        # Check notification sent
        notifications = self.notification_port.list_notifications()
        self.assertEqual(len(notifications), 1)
        self.assertEqual(notifications[0].type, "ReservationConfirmation")
        
        # 2. Advance time to pickup
        self.clock.set_time(pickup_time)
        
        # 3. Pickup vehicle
        rental = self.rental_service.pickup_vehicle(
            reservation, self.vehicle, Kilometers(10000), FuelLevel(0.8)
        )
        
        self.assertIsNotNone(rental)
        self.assertEqual(self.vehicle.status, VehicleStatus.RENTED)
        
        # 4. Advance time to return
        self.clock.set_time(return_time)
        
        # 5. Return vehicle (driven 500 km, fuel at 0.7)
        rental = self.rental_service.return_vehicle(
            rental.id, Kilometers(10500), FuelLevel(0.7)
        )
        
        self.assertTrue(rental.is_completed)
        self.assertGreater(len(rental.charge_items), 0)
        
        # 6. Create invoice and process payment
        invoice = self.accounting_service.create_invoice(rental)
        success = self.accounting_service.finalize_payment(invoice)
        
        self.assertTrue(success)
        self.assertEqual(invoice.status, "Paid")
        
        # Check payment notification sent
        payment_notifications = self.notification_port.get_notifications_by_type("InvoiceSuccess")
        self.assertEqual(len(payment_notifications), 1)
    
    def test_idempotent_pickup(self):
        """Test that pickup with same token returns same rental."""
        pickup_time = self.clock.now()
        return_time = pickup_time + timedelta(days=3)
        
        reservation = self.reservation_service.create_reservation(
            self.customer, self.vehicle_class, self.location,
            pickup_time, return_time
        )
        
        # First pickup with token
        token = "test-token-123"
        rental1 = self.rental_service.pickup_vehicle(
            reservation, self.vehicle, Kilometers(10000), FuelLevel(0.8), token
        )
        
        # Second pickup with same token should return same rental
        rental2 = self.rental_service.pickup_vehicle(
            reservation, self.vehicle, Kilometers(10000), FuelLevel(0.8), token
        )
        
        self.assertEqual(rental1.id, rental2.id)
        self.assertEqual(rental1.pickup_token, rental2.pickup_token)
    
    def test_maintenance_blocks_assignment(self):
        """Test that vehicles due for maintenance cannot be assigned."""
        # Register maintenance
        self.maintenance_service.register_maintenance_plan(
            self.vehicle, "Oil Change", Kilometers(10400), None
        )
        
        # Vehicle should not be assignable (within 500 km threshold)
        self.assertFalse(self.maintenance_service.can_vehicle_be_assigned(self.vehicle))
        
        # Try to pickup - should fail
        pickup_time = self.clock.now()
        return_time = pickup_time + timedelta(days=3)
        
        reservation = self.reservation_service.create_reservation(
            self.customer, self.vehicle_class, self.location,
            pickup_time, return_time
        )
        
        with self.assertRaises(ValueError):
            self.rental_service.pickup_vehicle(
                reservation, self.vehicle, Kilometers(10000), FuelLevel(0.8)
            )


if __name__ == '__main__':
    unittest.main()
