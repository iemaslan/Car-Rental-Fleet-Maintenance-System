"""
Test suite for rental lifecycle operations (pickup and return).
Tests verify idempotent pickup operations, return charge computation,
late fees, mileage overage, and fuel refill charges using fixed clock.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from domain.models import RentalAgreement, VehicleStatus
from domain.value_objects import Money, FuelLevel, Kilometers


class TestPickupOperations:
    """Test vehicle pickup operations and idempotency."""
    
    def test_successful_pickup(self, rental_service, basic_reservation, 
                              economy_vehicle, fixed_clock):
        """Test successful vehicle pickup creates rental agreement."""
        # Move clock to pickup time
        fixed_clock.set_time(basic_reservation.pickup_time)
        
        rental = rental_service.pickup_vehicle(
            reservation=basic_reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0),
            pickup_token="test-token-123"
        )
        
        assert rental is not None
        assert rental.id == 1
        assert rental.reservation == basic_reservation
        assert rental.vehicle == economy_vehicle
        assert rental.pickup_token == "test-token-123"
        assert rental.start_odometer == Kilometers(50000)
        assert rental.start_fuel_level == FuelLevel(1.0)
        assert not rental.is_completed
        
        # Vehicle should be marked as rented
        assert economy_vehicle.status == VehicleStatus.RENTED
    
    def test_pickup_idempotency_same_token(self, rental_service, basic_reservation, 
                                          economy_vehicle, fixed_clock):
        """
        Test pickup idempotency: calling pickup twice with same token
        returns same rental without duplicating charges or corrupting state.
        """
        fixed_clock.set_time(basic_reservation.pickup_time)
        
        # First pickup
        rental1 = rental_service.pickup_vehicle(
            reservation=basic_reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0),
            pickup_token="test-token-123"
        )
        
        # Second pickup with same token should return same rental
        rental2 = rental_service.pickup_vehicle(
            reservation=basic_reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0),
            pickup_token="test-token-123"
        )
        
        # Should be exact same rental
        assert rental1.id == rental2.id
        assert rental1.pickup_token == rental2.pickup_token
        
        # Verify no duplicate rental was created
        assert len(rental_service.rental_agreements) == 1
        
        # Vehicle should still be rented
        assert economy_vehicle.status == VehicleStatus.RENTED
    
    def test_pickup_generates_token_if_not_provided(self, rental_service, 
                                                   basic_reservation, 
                                                   economy_vehicle, fixed_clock):
        """Test pickup generates unique token when not provided."""
        fixed_clock.set_time(basic_reservation.pickup_time)
        
        rental = rental_service.pickup_vehicle(
            reservation=basic_reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0)
            # No pickup_token provided
        )
        
        assert rental.pickup_token is not None
        assert len(rental.pickup_token) > 0
    
    def test_pickup_fails_when_vehicle_unavailable(self, rental_service, 
                                                   basic_reservation, 
                                                   economy_vehicle, fixed_clock):
        """Test pickup fails when vehicle is not available."""
        fixed_clock.set_time(basic_reservation.pickup_time)
        economy_vehicle.status = VehicleStatus.OUT_OF_SERVICE
        
        with pytest.raises(ValueError, match="is not available"):
            rental_service.pickup_vehicle(
                reservation=basic_reservation,
                vehicle=economy_vehicle,
                start_odometer=Kilometers(50000),
                start_fuel_level=FuelLevel(1.0)
            )
    
    def test_pickup_fails_when_maintenance_due(self, rental_service, 
                                               basic_reservation, 
                                               economy_vehicle, 
                                               maintenance_service, 
                                               fixed_clock):
        """Test pickup fails when vehicle is due for maintenance."""
        fixed_clock.set_time(basic_reservation.pickup_time)
        
        # Register maintenance that's overdue
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(49500)  # Already passed
        )
        
        with pytest.raises(ValueError, match="due for maintenance"):
            rental_service.pickup_vehicle(
                reservation=basic_reservation,
                vehicle=economy_vehicle,
                start_odometer=Kilometers(50000),
                start_fuel_level=FuelLevel(1.0)
            )
    
    def test_pickup_with_agent(self, rental_service, basic_reservation, 
                              economy_vehicle, agent, fixed_clock):
        """Test pickup records agent information."""
        fixed_clock.set_time(basic_reservation.pickup_time)
        
        rental = rental_service.pickup_vehicle(
            reservation=basic_reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0),
            agent=agent
        )
        
        assert rental.pickup_agent == agent


class TestReturnOperations:
    """Test vehicle return operations and charge calculations."""
    
    def test_successful_return_on_time(self, active_rental_scenario):
        """Test successful on-time return computes all charges."""
        rental_service, rental, vehicle, fixed_clock = active_rental_scenario
        
        # Move clock to expected return time (on time)
        fixed_clock.set_time(rental.expected_return_time)
        
        # Return vehicle
        returned_rental = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50500),  # Drove 500 km
            end_fuel_level=FuelLevel(1.0)
        )
        
        assert returned_rental.is_completed
        assert returned_rental.actual_return_time == rental.expected_return_time
        assert returned_rental.end_odometer == Kilometers(50500)
        assert returned_rental.end_fuel_level == FuelLevel(1.0)
        
        # Should have charges computed
        assert len(returned_rental.charge_items) > 0
        
        # Vehicle should be in cleaning status
        assert vehicle.status == VehicleStatus.CLEANING
        assert vehicle.odometer == Kilometers(50500)
        assert vehicle.fuel_level == FuelLevel(1.0)
    
    def test_return_idempotency(self, active_rental_scenario):
        """Test return operation is idempotent."""
        rental_service, rental, vehicle, fixed_clock = active_rental_scenario
        
        fixed_clock.set_time(rental.expected_return_time)
        
        # First return
        returned1 = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50500),
            end_fuel_level=FuelLevel(1.0)
        )
        
        original_charges = len(returned1.charge_items)
        
        # Second return (should be idempotent)
        returned2 = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50500),
            end_fuel_level=FuelLevel(1.0)
        )
        
        # Same rental, same charges
        assert returned1.id == returned2.id
        assert len(returned2.charge_items) == original_charges
    
    def test_return_with_late_fee(self, active_rental_scenario):
        """Test return computes late fee for return after grace period."""
        rental_service, rental, vehicle, fixed_clock = active_rental_scenario
        
        # Return 3 hours late (beyond 1-hour grace period)
        late_return_time = rental.expected_return_time + timedelta(hours=3)
        fixed_clock.set_time(late_return_time)
        
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50500),
            end_fuel_level=FuelLevel(1.0)
        )
        
        # Find late fee charge
        late_fee_charges = [c for c in returned.charge_items if "Late fee" in c.description]
        assert len(late_fee_charges) == 1
        
        # 3 hours late - 1 hour grace = 2 hours @ $25/hour = $50
        assert late_fee_charges[0].amount == Money(Decimal('50.00'))
    
    def test_return_no_late_fee_within_grace_period(self, active_rental_scenario):
        """Test no late fee when return is within grace period."""
        rental_service, rental, vehicle, fixed_clock = active_rental_scenario
        
        # Return 30 minutes late (within 1-hour grace period)
        grace_return_time = rental.expected_return_time + timedelta(minutes=30)
        fixed_clock.set_time(grace_return_time)
        
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50500),
            end_fuel_level=FuelLevel(1.0)
        )
        
        # Should not have late fee charge
        late_fee_charges = [c for c in returned.charge_items if "Late fee" in c.description]
        assert len(late_fee_charges) == 0
    
    def test_return_with_mileage_overage(self, active_rental_scenario):
        """Test return computes mileage overage charge."""
        rental_service, rental, vehicle, fixed_clock = active_rental_scenario
        
        fixed_clock.set_time(rental.expected_return_time)
        
        # Economy class: 200 km/day allowance, 3 days = 600 km
        # Drive 900 km = 300 km overage
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50900),
            end_fuel_level=FuelLevel(1.0)
        )
        
        # Find mileage overage charge
        mileage_charges = [c for c in returned.charge_items if "Mileage overage" in c.description]
        assert len(mileage_charges) == 1
        
        # 300 km overage @ $0.50/km = $150
        assert mileage_charges[0].amount == Money(Decimal('150.00'))
    
    def test_return_no_mileage_overage_within_allowance(self, active_rental_scenario):
        """Test no mileage overage charge when within allowance."""
        rental_service, rental, vehicle, fixed_clock = active_rental_scenario
        
        fixed_clock.set_time(rental.expected_return_time)
        
        # Drive only 400 km (within 600 km allowance)
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50400),
            end_fuel_level=FuelLevel(1.0)
        )
        
        # Should not have mileage overage charge
        mileage_charges = [c for c in returned.charge_items if "Mileage overage" in c.description]
        assert len(mileage_charges) == 0
    
    def test_return_with_fuel_refill_charge(self, active_rental_scenario):
        """Test return computes fuel refill charge for lower fuel level."""
        rental_service, rental, vehicle, fixed_clock = active_rental_scenario
        
        fixed_clock.set_time(rental.expected_return_time)
        
        # Return with 60% fuel (started with 100%)
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50500),
            end_fuel_level=FuelLevel(0.6)
        )
        
        # Find fuel refill charge
        fuel_charges = [c for c in returned.charge_items if "Fuel refill" in c.description]
        assert len(fuel_charges) == 1
        
        # 40% fuel used = 4 units @ $10/10% = $40
        assert fuel_charges[0].amount == Money(Decimal('40.00'))
    
    def test_return_no_fuel_charge_same_level(self, active_rental_scenario):
        """Test no fuel charge when fuel level is same or higher."""
        rental_service, rental, vehicle, fixed_clock = active_rental_scenario
        
        fixed_clock.set_time(rental.expected_return_time)
        
        # Return with same fuel level
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50500),
            end_fuel_level=FuelLevel(1.0)
        )
        
        # Should not have fuel refill charge
        fuel_charges = [c for c in returned.charge_items if "Fuel refill" in c.description]
        assert len(fuel_charges) == 0
    
    def test_return_with_agent(self, active_rental_scenario, agent):
        """Test return records agent information."""
        rental_service, rental, vehicle, fixed_clock = active_rental_scenario
        
        fixed_clock.set_time(rental.expected_return_time)
        
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50500),
            end_fuel_level=FuelLevel(1.0),
            agent=agent
        )
        
        assert returned.return_agent == agent
    
    def test_return_computes_multiple_charges(self, active_rental_scenario):
        """Test return with multiple charge types: late, mileage, fuel."""
        rental_service, rental, vehicle, fixed_clock = active_rental_scenario
        
        # Return 5 hours late
        late_return_time = rental.expected_return_time + timedelta(hours=5)
        fixed_clock.set_time(late_return_time)
        
        # High mileage and low fuel
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(51000),  # 1000 km driven, 400 overage
            end_fuel_level=FuelLevel(0.5)     # 50% fuel used
        )
        
        # Should have all charge types
        late_fees = [c for c in returned.charge_items if "Late fee" in c.description]
        mileage_fees = [c for c in returned.charge_items if "Mileage" in c.description]
        fuel_fees = [c for c in returned.charge_items if "Fuel" in c.description]
        
        assert len(late_fees) == 1
        assert len(mileage_fees) == 1
        assert len(fuel_fees) == 1
        
        # Verify amounts
        # Late: 4 hours @ $25 = $100
        # Mileage: 400 km @ $0.50 = $200
        # Fuel: 5 units @ $10 = $50
        assert late_fees[0].amount == Money(Decimal('100.00'))
        assert mileage_fees[0].amount == Money(Decimal('200.00'))
        assert fuel_fees[0].amount == Money(Decimal('50.00'))


class TestRentalScenarios:
    """Test complete rental scenarios from pickup to return."""
    
    def test_short_rental_scenario(self, rental_service, economy_vehicle, 
                                   customer, economy_class, location, fixed_clock):
        """Test complete short (1-day) rental scenario."""
        # Create reservation for 1 day
        pickup_time = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup_time + timedelta(days=1)
        
        from domain.models import Reservation
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup_time, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        # Pickup
        fixed_clock.set_time(pickup_time)
        rental = rental_service.pickup_vehicle(
            reservation=reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0)
        )
        
        # Return on time
        fixed_clock.set_time(return_time)
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50150),  # 150 km, within allowance
            end_fuel_level=FuelLevel(1.0)
        )
        
        # Verify charges: only base rate
        assert returned.is_completed
        total = returned.total_charges()
        # Economy: $30/day * 1 = $30
        assert total == Money(Decimal('30.00'))
    
    def test_long_rental_scenario(self, rental_service, luxury_vehicle, 
                                 customer, luxury_class, location, fixed_clock):
        """Test complete long (14-day) luxury rental scenario."""
        pickup_time = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup_time + timedelta(days=14)
        
        from domain.models import Reservation
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=luxury_class,
            location=location, pickup_time=pickup_time, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        # Pickup
        fixed_clock.set_time(pickup_time)
        rental = rental_service.pickup_vehicle(
            reservation=reservation,
            vehicle=luxury_vehicle,
            start_odometer=Kilometers(15000),
            start_fuel_level=FuelLevel(1.0)
        )
        
        # Return on time
        fixed_clock.set_time(return_time)
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(19000),  # 4000 km within allowance (300*14=4200)
            end_fuel_level=FuelLevel(1.0)
        )
        
        assert returned.is_completed
        total = returned.total_charges()
        # Luxury: $120/day * 14 = $1680
        assert total == Money(Decimal('1680.00'))
    
    def test_rental_with_all_extras(self, rental_service, suv_vehicle, 
                                   customer, suv_class, location, 
                                   gps_addon, child_seat_addon, 
                                   premium_insurance, fixed_clock):
        """Test rental with add-ons and insurance."""
        pickup_time = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup_time + timedelta(days=5)
        
        from domain.models import Reservation
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=suv_class,
            location=location, pickup_time=pickup_time, return_time=return_time,
            addons=[gps_addon, child_seat_addon],
            insurance_tier=premium_insurance
        )
        
        # Pickup
        fixed_clock.set_time(pickup_time)
        rental = rental_service.pickup_vehicle(
            reservation=reservation,
            vehicle=suv_vehicle,
            start_odometer=Kilometers(30000),
            start_fuel_level=FuelLevel(1.0)
        )
        
        # Return on time
        fixed_clock.set_time(return_time)
        returned = rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(31000),  # Within allowance
            end_fuel_level=FuelLevel(1.0)
        )
        
        total = returned.total_charges()
        # SUV base: $70 * 5 = $350
        # GPS: $10 * 5 = $50
        # ChildSeat: $5 * 5 = $25
        # Premium insurance: $25 * 5 = $125
        # Total: $550
        assert total == Money(Decimal('550.00'))


@pytest.mark.parametrize("hours_late,expected_late_fee", [
    (0, "0.00"),      # On time
    (1, "0.00"),      # Within 1-hour grace period
    (2, "25.00"),     # 1 hour beyond grace @ $25/hour
    (3, "50.00"),     # 2 hours beyond grace
    (5, "100.00"),    # 4 hours beyond grace
    (25, "600.00"),   # 24 hours beyond grace (full day late)
])
def test_late_fee_scenarios(hours_late, expected_late_fee, 
                           active_rental_scenario):
    """Parametrized test for various late fee scenarios."""
    rental_service, rental, vehicle, fixed_clock = active_rental_scenario
    
    # Set return time based on hours late
    return_time = rental.expected_return_time + timedelta(hours=hours_late)
    fixed_clock.set_time(return_time)
    
    returned = rental_service.return_vehicle(
        rental_agreement_id=rental.id,
        end_odometer=Kilometers(50500),
        end_fuel_level=FuelLevel(1.0)
    )
    
    late_fees = [c for c in returned.charge_items if "Late fee" in c.description]
    
    expected_amount = Money(Decimal(expected_late_fee))
    if expected_amount.amount > 0:
        assert len(late_fees) == 1
        assert late_fees[0].amount == expected_amount
    else:
        assert len(late_fees) == 0


@pytest.mark.parametrize("km_driven,days,allowance_per_day,expected_overage_fee", [
    (400, 3, 200, "0.00"),      # 400 km, allowance 600, no overage
    (600, 3, 200, "0.00"),      # Exactly at allowance
    (800, 3, 200, "100.00"),    # 200 km overage @ $0.50
    (1000, 5, 200, "0.00"),     # 1000 km, allowance 1000, exactly at limit - no overage
    (1500, 5, 200, "250.00"),   # 500 km overage @ $0.50
    (300, 1, 200, "50.00"),     # 100 km overage on 1-day rental
])
def test_mileage_overage_scenarios(km_driven, days, allowance_per_day, 
                                  expected_overage_fee, rental_service, 
                                  economy_vehicle, customer, location, 
                                  fixed_clock):
    """Parametrized test for various mileage overage scenarios."""
    from domain.models import Reservation, VehicleClass
    
    vehicle_class = VehicleClass(
        name="TestClass",
        base_rate=Money(Decimal('30.00')),
        daily_mileage_allowance=allowance_per_day
    )
    economy_vehicle.vehicle_class = vehicle_class
    
    pickup_time = datetime(2025, 12, 10, 10, 0, 0)
    return_time = pickup_time + timedelta(days=days)
    
    reservation = Reservation(
        id=1, customer=customer, vehicle_class=vehicle_class,
        location=location, pickup_time=pickup_time, return_time=return_time,
        addons=[], insurance_tier=None
    )
    
    # Pickup
    fixed_clock.set_time(pickup_time)
    rental = rental_service.pickup_vehicle(
        reservation=reservation,
        vehicle=economy_vehicle,
        start_odometer=Kilometers(50000),
        start_fuel_level=FuelLevel(1.0)
    )
    
    # Return
    fixed_clock.set_time(return_time)
    returned = rental_service.return_vehicle(
        rental_agreement_id=rental.id,
        end_odometer=Kilometers(50000 + km_driven),
        end_fuel_level=FuelLevel(1.0)
    )
    
    mileage_fees = [c for c in returned.charge_items if "Mileage" in c.description]
    
    expected_amount = Money(Decimal(expected_overage_fee))
    if expected_amount.amount > 0:
        assert len(mileage_fees) == 1
        assert mileage_fees[0].amount == expected_amount
    else:
        assert len(mileage_fees) == 0
