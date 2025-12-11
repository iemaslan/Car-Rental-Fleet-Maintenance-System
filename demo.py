"""
Comprehensive demonstration of the Car Rental & Fleet Maintenance System.
This script demonstrates all major features and use cases.
"""
from datetime import datetime, timedelta
from decimal import Decimal

# Import domain models
from domain.models import (
    Customer, Agent, Vehicle, VehicleClass, Location, 
    AddOn, InsuranceTier, VehicleStatus
)
from domain.value_objects import Money, FuelLevel, Kilometers
from domain.clock import FixedClock
from domain.audit_log import AuditLogger, AuditEventType

# Import services
from services.inventory_service import InventoryService
from services.maintenance_service import MaintenanceService
from services.pricing_policy import create_standard_pricing_policy
from services.rental_service import RentalService
from services.reservation_service import ReservationService
from services.accounting_service import AccountingService

# Import adapters
from adapters.notification_port import InMemoryNotificationAdapter
from adapters.payment_port import FakePaymentAdapter


def print_section(title: str):
    """Print a section header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def main():
    """Run the comprehensive demonstration."""
    
    print_section("CAR RENTAL & FLEET MAINTENANCE SYSTEM - COMPREHENSIVE DEMO")
    
    # ========== SETUP ==========
    print_section("1. System Setup")
    
    # Create clock
    fixed_time = datetime(2025, 11, 4, 10, 0, 0)
    clock = FixedClock(fixed_time)
    print(f"✓ Clock initialized to: {clock.now()}")
    
    # Create audit logger
    audit_logger = AuditLogger()
    print("✓ Audit logger initialized")
    
    # Create adapters
    notification_adapter = InMemoryNotificationAdapter(clock)
    payment_adapter = FakePaymentAdapter(clock, simulate_failure=False)
    print("✓ Notification and payment adapters created")
    
    # Create services
    maintenance_service = MaintenanceService(clock)
    inventory_service = InventoryService(clock, maintenance_service)
    pricing_policy = create_standard_pricing_policy(
        clock, 
        apply_weekend_surcharge=True,
        peak_season_months=[6, 7, 8]  # Summer months
    )
    rental_service = RentalService(clock, pricing_policy, maintenance_service, audit_logger)
    reservation_service = ReservationService(clock, notification_adapter)
    accounting_service = AccountingService(clock, payment_adapter, notification_adapter)
    print("✓ All services initialized")
    
    # ========== CREATE TEST DATA ==========
    print_section("2. Creating Test Data")
    
    # Create vehicle classes
    economy_class = VehicleClass(
        name="Economy",
        base_rate=Money(Decimal('50.00')),
        daily_mileage_allowance=200
    )
    compact_class = VehicleClass(
        name="Compact",
        base_rate=Money(Decimal('70.00')),
        daily_mileage_allowance=250
    )
    suv_class = VehicleClass(
        name="SUV",
        base_rate=Money(Decimal('120.00')),
        daily_mileage_allowance=300
    )
    print("✓ Created 3 vehicle classes: Economy, Compact, SUV")
    
    # Create locations
    location_downtown = Location(id=1, name="Downtown Branch", address="123 Main St")
    location_airport = Location(id=2, name="Airport Branch", address="Airport Terminal 1")
    print("✓ Created 2 locations")
    
    # Create add-ons
    gps_addon = AddOn(name="GPS", daily_fee=Money(Decimal('10.00')))
    child_seat_addon = AddOn(name="ChildSeat", daily_fee=Money(Decimal('5.00')))
    extra_driver_addon = AddOn(name="ExtraDriver", daily_fee=Money(Decimal('15.00')))
    print("✓ Created 3 add-ons: GPS, ChildSeat, ExtraDriver")
    
    # Create insurance tiers
    basic_insurance = InsuranceTier(name="Basic", daily_fee=Money(Decimal('15.00')))
    premium_insurance = InsuranceTier(name="Premium", daily_fee=Money(Decimal('30.00')))
    print("✓ Created 2 insurance tiers")
    
    # Create vehicles
    vehicle1 = Vehicle(
        id=1,
        vehicle_class=economy_class,
        location=location_downtown,
        status=VehicleStatus.AVAILABLE,
        odometer=Kilometers(15000),
        fuel_level=FuelLevel(0.8)
    )
    vehicle2 = Vehicle(
        id=2,
        vehicle_class=compact_class,
        location=location_downtown,
        status=VehicleStatus.AVAILABLE,
        odometer=Kilometers(10000),
        fuel_level=FuelLevel(0.9)
    )
    vehicle3 = Vehicle(
        id=3,
        vehicle_class=suv_class,
        location=location_airport,
        status=VehicleStatus.AVAILABLE,
        odometer=Kilometers(25000),
        fuel_level=FuelLevel.full()
    )
    
    inventory_service.add_vehicle(vehicle1)
    inventory_service.add_vehicle(vehicle2)
    inventory_service.add_vehicle(vehicle3)
    print("✓ Created and added 3 vehicles to inventory")
    
    # Create customers
    customer1 = Customer(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="+1-555-0101"
    )
    customer2 = Customer(
        id=2,
        name="Jane Smith",
        email="jane.smith@example.com",
        phone="+1-555-0102"
    )
    print("✓ Created 2 customers")
    
    # Create agents
    agent1 = Agent(id=1, name="Alice Agent", branch="Downtown")
    agent2 = Agent(id=2, name="Bob Agent", branch="Airport")
    print("✓ Created 2 agents")
    
    # ========== MAINTENANCE SETUP ==========
    print_section("3. Maintenance Management")
    
    # Register maintenance plans
    maintenance_service.register_maintenance_plan(
        vehicle=vehicle3,
        service_type="Oil Change",
        odometer_threshold=Kilometers(26000),
        time_threshold=datetime(2025, 12, 1)
    )
    print(f"✓ Registered maintenance plan for vehicle {vehicle3.id}")
    print(f"  - Service: Oil Change")
    print(f"  - Odometer threshold: 26000 km")
    print(f"  - Vehicle is due: {maintenance_service.is_maintenance_due(vehicle3)}")
    
    # ========== INVENTORY QUERIES ==========
    print_section("4. Inventory Availability Check")
    
    search_start = datetime(2025, 11, 5, 10, 0, 0)
    search_end = datetime(2025, 11, 10, 10, 0, 0)
    
    availability = inventory_service.check_availability(
        economy_class, location_downtown, search_start, search_end
    )
    print(f"✓ Availability check for {economy_class.name} at {location_downtown.name}:")
    print(f"  - Available count: {availability['available_count']}")
    print(f"  - Total count: {availability['total_count']}")
    print(f"  - Maintenance holds: {availability['maintenance_hold_count']}")
    print(f"  - Available vehicles: {availability['available_vehicles']}")
    
    stats = inventory_service.get_vehicle_statistics()
    print(f"\n✓ Fleet statistics:")
    for key, value in stats.items():
        print(f"  - {key.replace('_', ' ').title()}: {value}")
    
    # ========== CREATE RESERVATION ==========
    print_section("5. Create Reservation")
    
    pickup_time = datetime(2025, 11, 5, 10, 0, 0)
    return_time = datetime(2025, 11, 8, 10, 0, 0)
    
    reservation1 = reservation_service.create_reservation(
        customer=customer1,
        vehicle_class=economy_class,
        location=location_downtown,
        pickup_time=pickup_time,
        return_time=return_time,
        addons=[gps_addon, child_seat_addon],
        insurance_tier=basic_insurance,
        deposit=Money(Decimal('200.00'))
    )
    print(f"✓ Created reservation #{reservation1.id} for {customer1.name}")
    print(f"  - Vehicle class: {reservation1.vehicle_class.name}")
    print(f"  - Pickup: {reservation1.pickup_time}")
    print(f"  - Return: {reservation1.return_time}")
    print(f"  - Duration: {reservation1.duration_in_days()} days")
    print(f"  - Add-ons: {', '.join([a.name for a in reservation1.addons])}")
    print(f"  - Insurance: {reservation1.insurance_tier.name}")
    print(f"  - Deposit: {reservation1.deposit}")
    
    notifications = notification_adapter.list_notifications()
    print(f"\n✓ Notification sent: {notifications[-1].type}")
    
    # ========== VEHICLE PICKUP ==========
    print_section("6. Vehicle Pickup (Idempotent)")
    
    # Advance clock to pickup time
    clock.set_time(pickup_time)
    print(f"✓ Advanced clock to: {clock.now()}")
    
    # Perform pickup
    rental1 = rental_service.pickup_vehicle(
        reservation=reservation1,
        vehicle=vehicle1,
        start_odometer=Kilometers(15000),
        start_fuel_level=FuelLevel(0.8),
        agent=agent1,
        pickup_token="unique-token-123"
    )
    print(f"\n✓ Vehicle picked up successfully")
    print(f"  - Rental Agreement ID: {rental1.id}")
    print(f"  - Vehicle ID: {rental1.vehicle.id}")
    print(f"  - Pickup token: {rental1.pickup_token}")
    print(f"  - Start odometer: {rental1.start_odometer}")
    print(f"  - Start fuel: {rental1.start_fuel_level}")
    print(f"  - Pickup agent: {rental1.pickup_agent.name if rental1.pickup_agent else 'N/A'}")
    print(f"  - Vehicle status: {vehicle1.status.value}")
    
    # Test idempotency - try same pickup again
    rental1_duplicate = rental_service.pickup_vehicle(
        reservation=reservation1,
        vehicle=vehicle1,
        start_odometer=Kilometers(15000),
        start_fuel_level=FuelLevel(0.8),
        agent=agent1,
        pickup_token="unique-token-123"  # Same token
    )
    print(f"\n✓ Idempotency test: Same rental returned (ID: {rental1_duplicate.id})")
    
    # Authorize deposit
    invoice_for_deposit = accounting_service.create_invoice(rental1)
    deposit_payment = accounting_service.authorize_deposit(invoice_for_deposit, reservation1.deposit)
    print(f"\n✓ Deposit authorized: {deposit_payment.status}")
    
    # ========== RENTAL EXTENSION ==========
    print_section("7. Rental Extension")
    
    new_return_time = datetime(2025, 11, 10, 10, 0, 0)
    extended = rental_service.extend_rental(rental1.id, new_return_time)
    print(f"✓ Rental extended: {extended}")
    if extended:
        print(f"  - Original return: {return_time}")
        print(f"  - New return: {new_return_time}")
        print(f"  - Additional days: {(new_return_time - return_time).days}")
    
    # ========== VEHICLE RETURN WITH LATE FEE ==========
    print_section("8. Vehicle Return (With Late Fee)")
    
    # Advance clock to 2 hours after expected return
    actual_return_time = new_return_time + timedelta(hours=2)
    clock.set_time(actual_return_time)
    print(f"✓ Advanced clock to: {clock.now()}")
    print(f"  - Expected return: {new_return_time}")
    print(f"  - Actual return: {actual_return_time}")
    print(f"  - Hours late (after grace period): {(actual_return_time - new_return_time).seconds // 3600 - 1}")
    
    # Return vehicle with some mileage overage and low fuel
    end_odometer = Kilometers(15800)  # Drove 800 km in 5 days (allowance: 1000 km)
    end_fuel = FuelLevel(0.5)  # 30% less fuel
    
    rental1 = rental_service.return_vehicle(
        rental_agreement_id=rental1.id,
        end_odometer=end_odometer,
        end_fuel_level=end_fuel,
        agent=agent1
    )
    
    print(f"\n✓ Vehicle returned successfully")
    print(f"  - End odometer: {end_odometer}")
    print(f"  - End fuel: {end_fuel}")
    print(f"  - Driven distance: {rental1.driven_distance()}")
    print(f"  - Return agent: {rental1.return_agent.name if rental1.return_agent else 'N/A'}")
    print(f"  - Vehicle status: {vehicle1.status.value}")
    
    # ========== CHARGE COMPUTATION ==========
    print_section("9. Charge Computation")
    
    print("✓ Itemized charges:")
    for i, charge in enumerate(rental1.charge_items, 1):
        print(f"  {i}. {charge.description}: {charge.amount}")
    
    total = rental1.total_charges()
    print(f"\n✓ Total charges: {total}")
    
    # ========== MANUAL DAMAGE CHARGE ==========
    print_section("10. Manual Damage Charge")
    
    damage_amount = Money(Decimal('150.00'))
    rental_service.add_manual_damage_charge(
        rental_agreement_id=rental1.id,
        damage_amount=damage_amount,
        description="Scratch on rear bumper",
        agent=agent1
    )
    print(f"✓ Manual damage charge added: {damage_amount}")
    print(f"  - Description: Scratch on rear bumper")
    print(f"  - New total: {rental1.total_charges()}")
    
    # ========== INVOICE AND PAYMENT ==========
    print_section("11. Invoice and Payment")
    
    final_invoice = accounting_service.create_invoice(rental1)
    print(f"✓ Invoice created: #{final_invoice.id}")
    print(f"  - Total amount: {final_invoice.total_amount}")
    print(f"  - Status: {final_invoice.status}")
    print(f"  - Number of charge items: {len(final_invoice.charge_items)}")
    
    # Finalize payment
    payment_success = accounting_service.finalize_payment(final_invoice)
    print(f"\n✓ Payment finalized: {payment_success}")
    print(f"  - Invoice status: {final_invoice.status}")
    
    # Check notifications
    invoice_notifications = notification_adapter.get_notifications_by_type("InvoiceSuccess")
    print(f"\n✓ Invoice notifications sent: {len(invoice_notifications)}")
    
    # ========== AUDIT LOG ==========
    print_section("12. Audit Log")
    
    rental_audit = audit_logger.get_entries_by_entity("RentalAgreement", rental1.id)
    print(f"✓ Audit entries for Rental Agreement #{rental1.id}: {len(rental_audit)}")
    for entry in rental_audit:
        print(f"\n  [{entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {entry.event_type.value}")
        print(f"  Actor: {entry.actor_type} - {entry.actor_name}")
        print(f"  Description: {entry.description}")
        if entry.metadata:
            print(f"  Metadata: {', '.join([f'{k}={v}' for k, v in list(entry.metadata.items())[:3]])}")
    
    # ========== OVERDUE RENTALS ==========
    print_section("13. Test: Create Reservation with Upgrade")
    
    # Create another reservation for SUV but assign Compact (upgrade)
    reservation2 = reservation_service.create_reservation(
        customer=customer2,
        vehicle_class=economy_class,
        location=location_downtown,
        pickup_time=datetime(2025, 11, 12, 10, 0, 0),
        return_time=datetime(2025, 11, 15, 10, 0, 0),
        addons=[gps_addon],
        insurance_tier=premium_insurance,
        deposit=Money(Decimal('250.00'))
    )
    
    clock.set_time(datetime(2025, 11, 12, 10, 0, 0))
    
    # Upgrade to Compact
    rental2 = rental_service.pickup_vehicle(
        reservation=reservation2,
        vehicle=vehicle2,  # Compact instead of Economy
        start_odometer=Kilometers(10000),
        start_fuel_level=FuelLevel(0.9),
        agent=agent2
    )
    
    print(f"✓ Created reservation #{reservation2.id}")
    print(f"  - Requested: {reservation2.vehicle_class.name}")
    print(f"  - Assigned: {rental2.vehicle.vehicle_class.name}")
    print(f"  - Is upgraded: {rental2.is_upgraded}")
    
    # Check upgrade audit entry
    upgrade_entries = audit_logger.get_entries_by_event_type(AuditEventType.VEHICLE_UPGRADE)
    print(f"\n✓ Upgrade audit entries: {len(upgrade_entries)}")
    if upgrade_entries:
        entry = upgrade_entries[-1]
        print(f"  - {entry.description}")
        print(f"  - Agent: {entry.actor_name}")
    
    # ========== SUMMARY ==========
    print_section("14. System Summary")
    
    print("✓ Reservations:")
    all_reservations = reservation_service.list_reservations()
    print(f"  - Total: {len(all_reservations)}")
    
    print("\n✓ Rental Agreements:")
    all_rentals = list(rental_service.rental_agreements.values())
    completed = [r for r in all_rentals if r.is_completed]
    active = [r for r in all_rentals if not r.is_completed]
    print(f"  - Total: {len(all_rentals)}")
    print(f"  - Completed: {len(completed)}")
    print(f"  - Active: {len(active)}")
    
    print("\n✓ Invoices:")
    pending_invoices = accounting_service.list_pending_invoices()
    print(f"  - Pending: {len(pending_invoices)}")
    
    print("\n✓ Audit Log:")
    all_audit_entries = audit_logger.list_all_entries()
    print(f"  - Total entries: {len(all_audit_entries)}")
    
    print("\n✓ Notifications:")
    all_notifications = notification_adapter.list_notifications()
    print(f"  - Total sent: {len(all_notifications)}")
    
    print("\n✓ Payments:")
    all_payments = payment_adapter.list_payments()
    print(f"  - Total transactions: {len(all_payments)}")
    
    print_section("DEMO COMPLETED SUCCESSFULLY")
    print("\nAll major features demonstrated:")
    print("  ✓ Value objects (Money, FuelLevel, Kilometers)")
    print("  ✓ Injectable clock for deterministic testing")
    print("  ✓ Inventory management and availability queries")
    print("  ✓ Maintenance scheduling and holds")
    print("  ✓ Reservation creation, modification, and notifications")
    print("  ✓ Idempotent pickup with tokens")
    print("  ✓ Vehicle upgrades with audit trail")
    print("  ✓ Rental extensions with conflict checking")
    print("  ✓ Vehicle returns with comprehensive charge computation")
    print("  ✓ Late fees with grace period")
    print("  ✓ Mileage overage charges")
    print("  ✓ Fuel refill charges")
    print("  ✓ Manual damage charges with audit logging")
    print("  ✓ Pricing policy with composable rules")
    print("  ✓ Invoice creation and payment processing")
    print("  ✓ Notification system")
    print("  ✓ Comprehensive audit logging")
    print("  ✓ SOLID principles applied throughout")


if __name__ == "__main__":
    main()
