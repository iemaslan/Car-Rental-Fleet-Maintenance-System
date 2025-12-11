"""
Shared pytest fixtures for the Car Rental & Fleet Maintenance System test suite.
Provides common domain objects, services, and test scenarios.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from domain.models import (
    Customer, Agent, VehicleClass, Vehicle, Location, 
    AddOn, InsuranceTier, Reservation, VehicleStatus
)
from domain.value_objects import Money, FuelLevel, Kilometers
from domain.clock import FixedClock
from domain.audit_log import AuditLogger

from services.pricing_policy import (
    PricingPolicy, create_standard_pricing_policy
)
from services.rental_service import RentalService
from services.maintenance_service import MaintenanceService
from services.reservation_service import ReservationService
from services.accounting_service import AccountingService

from adapters.payment_port import FakePaymentAdapter
from adapters.notification_port import InMemoryNotificationAdapter


# ============== Time Fixtures ==============

@pytest.fixture
def base_time():
    """Base datetime for deterministic testing."""
    return datetime(2025, 12, 10, 10, 0, 0)


@pytest.fixture
def fixed_clock(base_time):
    """Fixed clock for deterministic time-based testing."""
    return FixedClock(base_time)


# ============== Domain Entity Fixtures ==============

@pytest.fixture
def customer():
    """Standard customer fixture."""
    return Customer(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="+1234567890"
    )


@pytest.fixture
def agent():
    """Standard agent fixture."""
    return Agent(
        id=1,
        name="Alice Agent",
        branch="Downtown"
    )


@pytest.fixture
def location():
    """Standard location fixture."""
    return Location(
        id=1,
        name="Downtown Branch",
        address="123 Main St"
    )


# ============== Vehicle Class Fixtures ==============

@pytest.fixture
def economy_class():
    """Economy vehicle class."""
    return VehicleClass(
        name="Economy",
        base_rate=Money(Decimal('30.00')),
        daily_mileage_allowance=200
    )


@pytest.fixture
def compact_class():
    """Compact vehicle class."""
    return VehicleClass(
        name="Compact",
        base_rate=Money(Decimal('40.00')),
        daily_mileage_allowance=200
    )


@pytest.fixture
def suv_class():
    """SUV vehicle class."""
    return VehicleClass(
        name="SUV",
        base_rate=Money(Decimal('70.00')),
        daily_mileage_allowance=250
    )


@pytest.fixture
def luxury_class():
    """Luxury vehicle class."""
    return VehicleClass(
        name="Luxury",
        base_rate=Money(Decimal('120.00')),
        daily_mileage_allowance=300
    )


# ============== Vehicle Fixtures ==============

@pytest.fixture
def economy_vehicle(economy_class, location):
    """Available economy vehicle."""
    return Vehicle(
        id=1,
        vehicle_class=economy_class,
        location=location,
        status=VehicleStatus.AVAILABLE,
        odometer=Kilometers(50000),
        fuel_level=FuelLevel(1.0)
    )


@pytest.fixture
def suv_vehicle(suv_class, location):
    """Available SUV vehicle."""
    return Vehicle(
        id=2,
        vehicle_class=suv_class,
        location=location,
        status=VehicleStatus.AVAILABLE,
        odometer=Kilometers(30000),
        fuel_level=FuelLevel(1.0)
    )


@pytest.fixture
def luxury_vehicle(luxury_class, location):
    """Available luxury vehicle."""
    return Vehicle(
        id=3,
        vehicle_class=luxury_class,
        location=location,
        status=VehicleStatus.AVAILABLE,
        odometer=Kilometers(15000),
        fuel_level=FuelLevel(1.0)
    )


# ============== Add-On Fixtures ==============

@pytest.fixture
def gps_addon():
    """GPS add-on service."""
    return AddOn(name="GPS", daily_fee=Money(Decimal('10.00')))


@pytest.fixture
def child_seat_addon():
    """Child seat add-on service."""
    return AddOn(name="ChildSeat", daily_fee=Money(Decimal('5.00')))


@pytest.fixture
def extra_driver_addon():
    """Extra driver add-on service."""
    return AddOn(name="ExtraDriver", daily_fee=Money(Decimal('15.00')))


# ============== Insurance Tier Fixtures ==============

@pytest.fixture
def basic_insurance():
    """Basic insurance tier."""
    return InsuranceTier(name="Basic", daily_fee=Money(Decimal('10.00')))


@pytest.fixture
def premium_insurance():
    """Premium insurance tier."""
    return InsuranceTier(name="Premium", daily_fee=Money(Decimal('25.00')))


@pytest.fixture
def full_coverage_insurance():
    """Full coverage insurance tier."""
    return InsuranceTier(name="FullCoverage", daily_fee=Money(Decimal('40.00')))


# ============== Reservation Fixtures ==============

@pytest.fixture
def basic_reservation(customer, economy_class, location, base_time):
    """Basic 3-day economy reservation with no add-ons."""
    pickup = base_time + timedelta(days=1)
    return_time = pickup + timedelta(days=3)
    return Reservation(
        id=1,
        customer=customer,
        vehicle_class=economy_class,
        location=location,
        pickup_time=pickup,
        return_time=return_time,
        addons=[],
        insurance_tier=None,
        deposit=Money(Decimal('100.00'))
    )


@pytest.fixture
def reservation_with_addons(customer, suv_class, location, base_time, 
                          gps_addon, child_seat_addon, premium_insurance):
    """5-day SUV reservation with GPS, child seat, and premium insurance."""
    pickup = base_time + timedelta(days=1)
    return_time = pickup + timedelta(days=5)
    return Reservation(
        id=2,
        customer=customer,
        vehicle_class=suv_class,
        location=location,
        pickup_time=pickup,
        return_time=return_time,
        addons=[gps_addon, child_seat_addon],
        insurance_tier=premium_insurance,
        deposit=Money(Decimal('200.00'))
    )


# ============== Service Fixtures ==============

@pytest.fixture
def audit_logger():
    """Audit logger instance."""
    return AuditLogger()


@pytest.fixture
def standard_pricing_policy(fixed_clock):
    """Standard pricing policy with common rules."""
    return create_standard_pricing_policy(
        clock=fixed_clock,
        late_fee_per_hour=Money(Decimal('25.00')),
        mileage_overage_per_km=Money(Decimal('0.50')),
        fuel_refill_per_10pct=Money(Decimal('10.00')),
        apply_weekend_surcharge=False,
        peak_season_months=None
    )


@pytest.fixture
def weekend_pricing_policy(fixed_clock):
    """Pricing policy with weekend surcharge."""
    return create_standard_pricing_policy(
        clock=fixed_clock,
        late_fee_per_hour=Money(Decimal('25.00')),
        mileage_overage_per_km=Money(Decimal('0.50')),
        fuel_refill_per_10pct=Money(Decimal('10.00')),
        apply_weekend_surcharge=True,
        peak_season_months=None
    )


@pytest.fixture
def peak_season_pricing_policy(fixed_clock):
    """Pricing policy with peak season surcharge."""
    return create_standard_pricing_policy(
        clock=fixed_clock,
        late_fee_per_hour=Money(Decimal('25.00')),
        mileage_overage_per_km=Money(Decimal('0.50')),
        fuel_refill_per_10pct=Money(Decimal('10.00')),
        apply_weekend_surcharge=False,
        peak_season_months=[6, 7, 8]  # Summer months
    )


@pytest.fixture
def maintenance_service(fixed_clock):
    """Maintenance service instance."""
    return MaintenanceService(clock=fixed_clock)


@pytest.fixture
def rental_service(fixed_clock, standard_pricing_policy, maintenance_service, audit_logger):
    """Rental service with standard configuration."""
    return RentalService(
        clock=fixed_clock,
        pricing_policy=standard_pricing_policy,
        maintenance_service=maintenance_service,
        audit_logger=audit_logger
    )


@pytest.fixture
def payment_adapter(fixed_clock):
    """Fake payment adapter."""
    return FakePaymentAdapter(clock=fixed_clock, simulate_failure=False)


@pytest.fixture
def notification_adapter(fixed_clock):
    """In-memory notification adapter."""
    return InMemoryNotificationAdapter(clock=fixed_clock)


@pytest.fixture
def reservation_service(fixed_clock, notification_adapter):
    """Reservation service instance."""
    return ReservationService(
        clock=fixed_clock,
        notification_port=notification_adapter
    )


@pytest.fixture
def accounting_service(fixed_clock, payment_adapter, notification_adapter):
    """Accounting service instance."""
    return AccountingService(
        clock=fixed_clock,
        payment_port=payment_adapter,
        notification_port=notification_adapter
    )


# ============== Scenario Fixtures ==============

@pytest.fixture
def active_rental_scenario(rental_service, basic_reservation, economy_vehicle, fixed_clock):
    """
    Scenario with an active rental.
    Returns (rental_service, rental_agreement, vehicle, clock).
    """
    # Move clock to pickup time
    fixed_clock.set_time(basic_reservation.pickup_time)
    
    # Perform pickup
    rental_agreement = rental_service.pickup_vehicle(
        reservation=basic_reservation,
        vehicle=economy_vehicle,
        start_odometer=Kilometers(50000),
        start_fuel_level=FuelLevel(1.0)
    )
    
    return rental_service, rental_agreement, economy_vehicle, fixed_clock


@pytest.fixture
def completed_rental_scenario(active_rental_scenario):
    """
    Scenario with a completed rental (on-time return).
    Returns (rental_service, rental_agreement, vehicle, clock).
    """
    rental_service, rental_agreement, vehicle, fixed_clock = active_rental_scenario
    
    # Move clock to expected return time
    fixed_clock.set_time(rental_agreement.expected_return_time)
    
    # Return vehicle
    rental_service.return_vehicle(
        rental_agreement_id=rental_agreement.id,
        end_odometer=Kilometers(50500),
        end_fuel_level=FuelLevel(1.0)
    )
    
    return rental_service, rental_agreement, vehicle, fixed_clock
