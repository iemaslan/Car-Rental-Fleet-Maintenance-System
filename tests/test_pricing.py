"""
Test suite for pricing logic and charge computation.
Tests verify base rates, add-ons, insurance, dynamic factors (weekend/peak), and edge cases.
Uses parametrized tests to cover different combinations systematically.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from domain.models import Reservation, RentalAgreement, VehicleClass, Vehicle, VehicleStatus
from domain.value_objects import Money, FuelLevel, Kilometers
from services.pricing_policy import (
    BaseRateRule, AddOnRule, InsuranceRule, LateFeeRule,
    MileageOverageRule, FuelRefillRule, WeekendMultiplierRule,
    SeasonMultiplierRule, PricingPolicy, create_standard_pricing_policy
)


class TestBasicPricing:
    """Test basic pricing rules without add-ons or special conditions."""
    
    def test_base_rate_calculation(self, fixed_clock, economy_class, location, customer):
        """Test base daily rate calculation for economy class."""
        # 3-day rental
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time
        )
        
        rule = BaseRateRule()
        charges = rule.calculate(rental, fixed_clock)
        
        assert len(charges) == 1
        # Economy: $30/day * 3 days = $90
        assert charges[0].amount == Money(Decimal('90.00'))
        assert "3 days" in charges[0].description
    
    def test_minimum_duration_rental(self, fixed_clock, economy_class, location, customer):
        """Test edge case: minimum 1-day rental."""
        # 4-hour rental (should charge for 1 day minimum)
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(hours=4)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time
        )
        
        rule = BaseRateRule()
        charges = rule.calculate(rental, fixed_clock)
        
        # Should charge for minimum 1 day
        assert charges[0].amount == Money(Decimal('30.00'))
    
    def test_unusually_long_rental(self, fixed_clock, luxury_class, location, customer):
        """Test edge case: unusually long (30-day) luxury rental."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=30)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=luxury_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=luxury_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(10000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(10000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time
        )
        
        rule = BaseRateRule()
        charges = rule.calculate(rental, fixed_clock)
        
        # Luxury: $120/day * 30 days = $3600
        assert charges[0].amount == Money(Decimal('3600.00'))


class TestAddOnsAndInsurance:
    """Test add-on and insurance pricing."""
    
    def test_single_addon_pricing(self, fixed_clock, economy_class, location, 
                                  customer, gps_addon):
        """Test pricing with single add-on (GPS)."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[gps_addon], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time
        )
        
        rule = AddOnRule()
        charges = rule.calculate(rental, fixed_clock)
        
        assert len(charges) == 1
        # GPS: $10/day * 3 days = $30
        assert charges[0].amount == Money(Decimal('30.00'))
        assert "GPS" in charges[0].description
    
    def test_multiple_addons_pricing(self, fixed_clock, suv_class, location, 
                                    customer, gps_addon, child_seat_addon, 
                                    extra_driver_addon):
        """Test pricing with multiple add-ons."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=5)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=suv_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[gps_addon, child_seat_addon, extra_driver_addon],
            insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=suv_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(30000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(30000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time
        )
        
        rule = AddOnRule()
        charges = rule.calculate(rental, fixed_clock)
        
        assert len(charges) == 3
        # GPS: $10/day * 5 = $50
        # ChildSeat: $5/day * 5 = $25
        # ExtraDriver: $15/day * 5 = $75
        total = sum(charge.amount for charge in charges)
        assert total == Money(Decimal('150.00'))
    
    def test_insurance_tier_pricing(self, fixed_clock, economy_class, location, 
                                   customer, premium_insurance):
        """Test insurance tier pricing."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=premium_insurance
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time
        )
        
        rule = InsuranceRule()
        charges = rule.calculate(rental, fixed_clock)
        
        assert len(charges) == 1
        # Premium: $25/day * 3 days = $75
        assert charges[0].amount == Money(Decimal('75.00'))
        assert "Premium" in charges[0].description


@pytest.mark.parametrize("vehicle_class_name,base_rate,days,expected_base_total", [
    ("Economy", "30.00", 3, "90.00"),
    ("Economy", "30.00", 7, "210.00"),
    ("Compact", "40.00", 3, "120.00"),
    ("SUV", "70.00", 5, "350.00"),
    ("Luxury", "120.00", 2, "240.00"),
    ("Luxury", "120.00", 10, "1200.00"),
])
def test_base_rate_combinations(vehicle_class_name, base_rate, days, expected_base_total,
                                fixed_clock, location, customer):
    """Parametrized test for different vehicle classes and rental durations."""
    vehicle_class = VehicleClass(
        name=vehicle_class_name,
        base_rate=Money(Decimal(base_rate)),
        daily_mileage_allowance=200
    )
    
    pickup = datetime(2025, 12, 10, 10, 0, 0)
    return_time = pickup + timedelta(days=days)
    
    reservation = Reservation(
        id=1, customer=customer, vehicle_class=vehicle_class,
        location=location, pickup_time=pickup, return_time=return_time,
        addons=[], insurance_tier=None
    )
    
    vehicle = Vehicle(
        id=1, vehicle_class=vehicle_class, location=location,
        status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
        fuel_level=FuelLevel(1.0)
    )
    
    rental = RentalAgreement(
        id=1, reservation=reservation, vehicle=vehicle,
        pickup_token="test-token", start_odometer=Kilometers(50000),
        start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
        expected_return_time=return_time
    )
    
    rule = BaseRateRule()
    charges = rule.calculate(rental, fixed_clock)
    
    assert charges[0].amount == Money(Decimal(expected_base_total))


@pytest.mark.parametrize("addons_config,days,expected_total", [
    # (GPS only, 3 days) = 10*3 = 30
    ([("GPS", "10.00")], 3, "30.00"),
    # (GPS + ChildSeat, 5 days) = (10+5)*5 = 75
    ([("GPS", "10.00"), ("ChildSeat", "5.00")], 5, "75.00"),
    # (GPS + ChildSeat + ExtraDriver, 7 days) = (10+5+15)*7 = 210
    ([("GPS", "10.00"), ("ChildSeat", "5.00"), ("ExtraDriver", "15.00")], 7, "210.00"),
    # (No addons, 3 days) = 0
    ([], 3, "0.00"),
])
def test_addon_combinations(addons_config, days, expected_total,
                           fixed_clock, economy_class, location, customer):
    """Parametrized test for different add-on combinations."""
    from domain.models import AddOn
    
    addons = [AddOn(name=name, daily_fee=Money(Decimal(fee))) 
             for name, fee in addons_config]
    
    pickup = datetime(2025, 12, 10, 10, 0, 0)
    return_time = pickup + timedelta(days=days)
    
    reservation = Reservation(
        id=1, customer=customer, vehicle_class=economy_class,
        location=location, pickup_time=pickup, return_time=return_time,
        addons=addons, insurance_tier=None
    )
    
    vehicle = Vehicle(
        id=1, vehicle_class=economy_class, location=location,
        status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
        fuel_level=FuelLevel(1.0)
    )
    
    rental = RentalAgreement(
        id=1, reservation=reservation, vehicle=vehicle,
        pickup_token="test-token", start_odometer=Kilometers(50000),
        start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
        expected_return_time=return_time
    )
    
    rule = AddOnRule()
    charges = rule.calculate(rental, fixed_clock)
    
    total = sum(charge.amount for charge in charges) if charges else Money.zero()
    assert total == Money(Decimal(expected_total))


@pytest.mark.parametrize("insurance_name,daily_fee,days,expected_total", [
    ("Basic", "10.00", 3, "30.00"),
    ("Premium", "25.00", 5, "125.00"),
    ("FullCoverage", "40.00", 7, "280.00"),
    (None, None, 3, "0.00"),  # No insurance
])
def test_insurance_tier_combinations(insurance_name, daily_fee, days, expected_total,
                                    fixed_clock, economy_class, location, customer):
    """Parametrized test for different insurance tiers."""
    from domain.models import InsuranceTier
    
    insurance = None
    if insurance_name:
        insurance = InsuranceTier(name=insurance_name, daily_fee=Money(Decimal(daily_fee)))
    
    pickup = datetime(2025, 12, 10, 10, 0, 0)
    return_time = pickup + timedelta(days=days)
    
    reservation = Reservation(
        id=1, customer=customer, vehicle_class=economy_class,
        location=location, pickup_time=pickup, return_time=return_time,
        addons=[], insurance_tier=insurance
    )
    
    vehicle = Vehicle(
        id=1, vehicle_class=economy_class, location=location,
        status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
        fuel_level=FuelLevel(1.0)
    )
    
    rental = RentalAgreement(
        id=1, reservation=reservation, vehicle=vehicle,
        pickup_token="test-token", start_odometer=Kilometers(50000),
        start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
        expected_return_time=return_time
    )
    
    rule = InsuranceRule()
    charges = rule.calculate(rental, fixed_clock)
    
    total = sum(charge.amount for charge in charges) if charges else Money.zero()
    assert total == Money(Decimal(expected_total))


class TestDynamicFactors:
    """Test dynamic pricing factors (weekend and peak season)."""
    
    def test_weekend_surcharge_saturday_pickup(self, fixed_clock, economy_class, 
                                              location, customer):
        """Test weekend surcharge for Saturday pickup."""
        # December 13, 2025 is a Saturday
        pickup = datetime(2025, 12, 13, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time
        )
        
        rule = WeekendMultiplierRule(multiplier=1.2)
        charges = rule.calculate(rental, fixed_clock)
        
        assert len(charges) == 1
        # Base: $30 * 3 = $90, surcharge: $90 * 0.2 = $18
        assert abs(charges[0].amount.amount - Decimal('18.00')) < Decimal('0.01')
        assert "Weekend" in charges[0].description
    
    def test_no_weekend_surcharge_weekday(self, fixed_clock, economy_class, 
                                         location, customer):
        """Test no weekend surcharge for weekday pickup."""
        # December 10, 2025 is a Wednesday
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time
        )
        
        rule = WeekendMultiplierRule(multiplier=1.2)
        charges = rule.calculate(rental, fixed_clock)
        
        # No surcharge on weekdays
        assert len(charges) == 0
    
    def test_peak_season_surcharge(self, fixed_clock, economy_class, location, customer):
        """Test peak season surcharge for summer month."""
        # July 15, 2025 is in peak season
        pickup = datetime(2025, 7, 15, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time
        )
        
        rule = SeasonMultiplierRule(peak_months=[6, 7, 8], multiplier=1.3)
        charges = rule.calculate(rental, fixed_clock)
        
        assert len(charges) == 1
        # Base: $30 * 3 = $90, surcharge: $90 * 0.3 = $27
        assert abs(charges[0].amount.amount - Decimal('27.00')) < Decimal('0.01')
        assert "Peak season" in charges[0].description
    
    def test_no_peak_season_surcharge_off_season(self, fixed_clock, economy_class, 
                                                 location, customer):
        """Test no peak season surcharge for off-season month."""
        # December is not in peak season (June-August)
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time
        )
        
        rule = SeasonMultiplierRule(peak_months=[6, 7, 8], multiplier=1.3)
        charges = rule.calculate(rental, fixed_clock)
        
        # No surcharge in off-season
        assert len(charges) == 0


class TestLateFeeCalculation:
    """Test late fee calculation with grace period."""
    
    def test_late_fee_beyond_grace_period(self, fixed_clock, economy_class, 
                                         location, customer):
        """Test late fee for return 3 hours late (beyond 1-hour grace period)."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        expected_return = pickup + timedelta(days=3)
        actual_return = expected_return + timedelta(hours=3)  # 3 hours late
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=expected_return,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=expected_return,
            actual_return_time=actual_return
        )
        
        rule = LateFeeRule(hourly_rate=Money(Decimal('25.00')), grace_period_hours=1)
        charges = rule.calculate(rental, fixed_clock)
        
        assert len(charges) == 1
        # 3 hours late - 1 hour grace = 2 hours @ $25/hour = $50
        assert charges[0].amount == Money(Decimal('50.00'))
        assert "2 hours" in charges[0].description
    
    def test_no_late_fee_within_grace_period(self, fixed_clock, economy_class, 
                                            location, customer):
        """Test no late fee for return within grace period."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        expected_return = pickup + timedelta(days=3)
        actual_return = expected_return + timedelta(minutes=30)  # 30 min late
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=expected_return,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=expected_return,
            actual_return_time=actual_return
        )
        
        rule = LateFeeRule(hourly_rate=Money(Decimal('25.00')), grace_period_hours=1)
        charges = rule.calculate(rental, fixed_clock)
        
        # Within grace period, no late fee
        assert len(charges) == 0


class TestMileageAndFuelCharges:
    """Test mileage overage and fuel refill charges."""
    
    def test_mileage_overage_charge(self, fixed_clock, economy_class, location, customer):
        """Test mileage overage charge for exceeding daily allowance."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        # Economy allows 200 km/day, 3 days = 600 km allowance
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time,
            end_odometer=Kilometers(50800)  # Drove 800 km, 200 km overage
        )
        
        rule = MileageOverageRule(per_km_rate=Money(Decimal('0.50')))
        charges = rule.calculate(rental, fixed_clock)
        
        assert len(charges) == 1
        # 200 km overage @ $0.50/km = $100
        assert charges[0].amount == Money(Decimal('100.00'))
        assert "200 km" in charges[0].description
    
    def test_no_mileage_overage_within_allowance(self, fixed_clock, economy_class, 
                                                location, customer):
        """Test no mileage charge when within allowance."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time,
            end_odometer=Kilometers(50500)  # Drove 500 km, within 600 km allowance
        )
        
        rule = MileageOverageRule(per_km_rate=Money(Decimal('0.50')))
        charges = rule.calculate(rental, fixed_clock)
        
        # No overage
        assert len(charges) == 0
    
    def test_fuel_refill_charge(self, fixed_clock, economy_class, location, customer):
        """Test fuel refill charge for lower fuel level at return."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=return_time,
            end_fuel_level=FuelLevel(0.6)  # Returned at 60%, down from 100%
        )
        
        rule = FuelRefillRule(per_level_charge=Money(Decimal('10.00')))
        charges = rule.calculate(rental, fixed_clock)
        
        assert len(charges) == 1
        # 40% difference = 4 units of 10%, @ $10 per 10% = $40
        assert charges[0].amount == Money(Decimal('40.00'))
    
    def test_no_fuel_charge_same_or_higher_level(self, fixed_clock, economy_class, 
                                                 location, customer):
        """Test no fuel charge when fuel level is same or higher."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(0.8)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(0.8), pickup_time=pickup,
            expected_return_time=return_time,
            end_fuel_level=FuelLevel(1.0)  # Returned with more fuel
        )
        
        rule = FuelRefillRule(per_level_charge=Money(Decimal('10.00')))
        charges = rule.calculate(rental, fixed_clock)
        
        # No refill charge
        assert len(charges) == 0


class TestCompletePricingPolicy:
    """Test complete pricing policy with all rules combined."""
    
    def test_complete_pricing_all_charges(self, fixed_clock, economy_class, 
                                         location, customer, gps_addon, 
                                         basic_insurance):
        """Test complete pricing with base, add-on, insurance, late fee, mileage, and fuel."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        expected_return = pickup + timedelta(days=3)
        actual_return = expected_return + timedelta(hours=3)  # 3 hours late
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=expected_return,
            addons=[gps_addon], insurance_tier=basic_insurance
        )
        
        vehicle = Vehicle(
            id=1, vehicle_class=economy_class, location=location,
            status=VehicleStatus.AVAILABLE, odometer=Kilometers(50000),
            fuel_level=FuelLevel(1.0)
        )
        
        rental = RentalAgreement(
            id=1, reservation=reservation, vehicle=vehicle,
            pickup_token="test-token", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), pickup_time=pickup,
            expected_return_time=expected_return,
            actual_return_time=actual_return,
            end_odometer=Kilometers(50800),  # 800 km, 200 over allowance
            end_fuel_level=FuelLevel(0.7)    # 30% fuel used
        )
        
        policy = create_standard_pricing_policy(
            clock=fixed_clock,
            late_fee_per_hour=Money(Decimal('25.00')),
            mileage_overage_per_km=Money(Decimal('0.50')),
            fuel_refill_per_10pct=Money(Decimal('10.00'))
        )
        
        charges = policy.calculate_charges(rental)
        total = policy.calculate_total(rental)
        
        # Base: $30 * 3 = $90
        # GPS: $10 * 3 = $30
        # Insurance: $10 * 3 = $30
        # Late fee: 2 hours @ $25 = $50
        # Mileage: 200 km @ $0.50 = $100
        # Fuel: 3 units @ $10 = $30
        # Total = $330
        assert total == Money(Decimal('330.00'))
        assert len(charges) == 6
