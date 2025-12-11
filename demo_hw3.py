"""
Demo script for HW3: File Operations & Protocol Buffers
Demonstrates JSON and Protobuf persistence with sample CRFMS data.
"""
from datetime import datetime, timedelta
from persistence.json_persistence import JSONPersistence
from persistence.protobuf_persistence import ProtobufPersistence

from domain.models import (
    Customer, Vehicle, VehicleClass, VehicleStatus, Location,
    Reservation, RentalAgreement, MaintenanceRecord,
    Invoice, Payment, Notification, ChargeItem
)
from domain.value_objects import Money, FuelLevel, Kilometers


def create_sample_data():
    """Create sample CRFMS data for demonstration."""
    
    now = datetime(2024, 12, 11, 10, 0, 0)
    
    # Create customers
    customers = [
        Customer(id=1, name="John Doe", email="john.doe@email.com", phone="+1-555-0101"),
        Customer(id=2, name="Jane Smith", email="jane.smith@email.com", phone="+1-555-0102"),
        Customer(id=3, name="Bob Johnson", email="bob.j@email.com", phone="+1-555-0103"),
    ]
    
    # Create vehicle classes
    compact = VehicleClass("COMPACT", Money(30.00), 100)
    sedan = VehicleClass("SEDAN", Money(50.00), 120)
    suv = VehicleClass("SUV", Money(75.00), 150)
    luxury = VehicleClass("LUXURY", Money(120.00), 100)
    
    # Create locations
    downtown = Location(id=1, name="Downtown", address="123 Main St")
    airport = Location(id=2, name="Airport", address="456 Airport Rd")
    
    # Create vehicles
    vehicles = [
        Vehicle(id=1, vehicle_class=compact, location=downtown, status=VehicleStatus.AVAILABLE, odometer=Kilometers(15000), fuel_level=FuelLevel.FULL),
        Vehicle(id=2, vehicle_class=compact, location=downtown, status=VehicleStatus.AVAILABLE, odometer=Kilometers(22000), fuel_level=FuelLevel.FULL),
        Vehicle(id=3, vehicle_class=sedan, location=downtown, status=VehicleStatus.RENTED, odometer=Kilometers(35000), fuel_level=FuelLevel.THREE_QUARTERS),
        Vehicle(id=4, vehicle_class=sedan, location=airport, status=VehicleStatus.AVAILABLE, odometer=Kilometers(18000), fuel_level=FuelLevel.FULL),
        Vehicle(id=5, vehicle_class=suv, location=airport, status=VehicleStatus.RENTED, odometer=Kilometers(45000), fuel_level=FuelLevel.HALF),
        Vehicle(id=6, vehicle_class=suv, location=downtown, status=VehicleStatus.OUT_OF_SERVICE, odometer=Kilometers(78000), fuel_level=FuelLevel.QUARTER),
        Vehicle(id=7, vehicle_class=luxury, location=downtown, status=VehicleStatus.AVAILABLE, odometer=Kilometers(12000), fuel_level=FuelLevel.FULL),
        Vehicle(id=8, vehicle_class=luxury, location=airport, status=VehicleStatus.RENTED, odometer=Kilometers(8000), fuel_level=FuelLevel.FULL),
    ]
    
    # Create reservations
    reservations = [
        Reservation(
            id=1, customer=customers[0], vehicle_class=sedan, location=downtown,
            pickup_time=now, return_time=now + timedelta(days=3), addons=[], insurance_tier=None
        ),
        Reservation(
            id=2, customer=customers[1], vehicle_class=suv, location=airport,
            pickup_time=now + timedelta(days=1), return_time=now + timedelta(days=5), addons=[], insurance_tier=None
        ),
        Reservation(
            id=3, customer=customers[2], vehicle_class=luxury, location=downtown,
            pickup_time=now + timedelta(days=2), return_time=now + timedelta(days=4), addons=[], insurance_tier=None
        ),
    ]
    
    # Create rental agreements
    rentals = [
        RentalAgreement(
            id=1, reservation=reservations[0], vehicle=vehicles[2], pickup_token="TOKEN123",
            start_odometer=Kilometers(35000), end_odometer=Kilometers(35450),
            start_fuel_level=FuelLevel.FULL, end_fuel_level=FuelLevel.THREE_QUARTERS,
            pickup_time=now, expected_return_time=now + timedelta(days=3),
            actual_return_time=now + timedelta(days=3, hours=2),
            charge_items=[
                ChargeItem("Base Rental (3 days)", Money(150.00)),
                ChargeItem("Fuel Charge", Money(25.00)),
                ChargeItem("Late Return", Money(20.00)),
            ]
        ),
        RentalAgreement(
            id=2, reservation=reservations[1], vehicle=vehicles[4], pickup_token="TOKEN456",
            start_odometer=Kilometers(45000), end_odometer=None,
            start_fuel_level=FuelLevel.FULL, end_fuel_level=None,
            pickup_time=now + timedelta(days=1), expected_return_time=now + timedelta(days=5),
            actual_return_time=None,
            charge_items=[ChargeItem("Base Rental (4 days)", Money(300.00))]
        ),
        RentalAgreement(
            id=3, reservation=reservations[2], vehicle=vehicles[7], pickup_token="TOKEN789",
            start_odometer=Kilometers(8000), end_odometer=None,
            start_fuel_level=FuelLevel.FULL, end_fuel_level=None,
            pickup_time=now + timedelta(days=2), expected_return_time=now + timedelta(days=4),
            actual_return_time=None,
            charge_items=[ChargeItem("Base Rental (2 days)", Money(240.00))]
        ),
    ]
    
    # Create maintenance records
    maintenance = [
        MaintenanceRecord(
            id=1, vehicle=vehicles[5], service_type="OIL_CHANGE",
            odometer_threshold=Kilometers(80000), time_threshold=now + timedelta(days=90),
            last_service_date=now - timedelta(days=180), last_service_odometer=Kilometers(73000)
        ),
        MaintenanceRecord(
            id=2, vehicle=vehicles[2], service_type="TIRE_ROTATION",
            odometer_threshold=Kilometers(40000), time_threshold=None,
            last_service_date=now - timedelta(days=120), last_service_odometer=Kilometers(30000)
        ),
    ]
    
    # Create invoices
    invoices = [
        Invoice(
            id=1, rental_agreement=rentals[0], charge_items=rentals[0].charge_items,
            total_amount=Money(195.00), status="Paid", created_at=now + timedelta(days=3, hours=3)
        ),
        Invoice(
            id=2, rental_agreement=rentals[1], charge_items=rentals[1].charge_items,
            total_amount=Money(300.00), status="Pending", created_at=now + timedelta(days=1, hours=1)
        ),
    ]
    
    # Create payments
    payments = [
        Payment(
            id=1, invoice=invoices[0], amount=Money(195.00),
            status="Captured", timestamp=now + timedelta(days=3, hours=3, minutes=15)
        ),
    ]
    
    # Create notifications
    notifications = [
        Notification(
            type="ReservationConfirmation", recipient="john.doe@email.com",
            message="Your reservation has been confirmed", timestamp=now
        ),
        Notification(
            type="PickupReminder", recipient="jane.smith@email.com",
            message="Reminder: Your rental pickup is tomorrow", timestamp=now + timedelta(hours=12)
        ),
        Notification(
            type="InvoiceSuccess", recipient="bob.j@email.com",
            message="Invoice is ready", timestamp=now + timedelta(days=1, hours=2)
        ),
    ]
    
    return {
        'customers': customers,
        'vehicles': vehicles,
        'reservations': reservations,
        'rental_agreements': rentals,
        'maintenance_records': maintenance,
        'invoices': invoices,
        'payments': payments,
        'notifications': notifications,
    }


def main():
    print("=" * 70)
    print("HW3 Demo: File Operations & Protocol Buffers")
    print("=" * 70)
    print()
    
    # Create sample data
    print("📊 Creating sample CRFMS data...")
    data = create_sample_data()
    print(f"   ✓ {len(data['customers'])} customers")
    print(f"   ✓ {len(data['vehicles'])} vehicles")
    print(f"   ✓ {len(data['reservations'])} reservations")
    print(f"   ✓ {len(data['rental_agreements'])} rental agreements")
    print(f"   ✓ {len(data['maintenance_records'])} maintenance records")
    print(f"   ✓ {len(data['invoices'])} invoices")
    print(f"   ✓ {len(data['payments'])} payments")
    print(f"   ✓ {len(data['notifications'])} notifications")
    print()
    
    # Save to JSON
    json_file = "snapshots/demo_snapshot.json"
    print(f"💾 Saving to JSON: {json_file}")
    JSONPersistence.save_snapshot(
        filename=json_file,
        **data
    )
    print(f"   ✓ Saved successfully")
    print()
    
    # Save to Protobuf
    proto_file = "snapshots/demo_snapshot.pb"
    print(f"💾 Saving to Protobuf: {proto_file}")
    ProtobufPersistence.save_snapshot(
        filename=proto_file,
        **data
    )
    print(f"   ✓ Saved successfully")
    print()
    
    # Load from JSON
    print(f"📂 Loading from JSON: {json_file}")
    json_data = JSONPersistence.load_snapshot(json_file)
    print(f"   ✓ Loaded {len(json_data['customers'])} customers")
    print()
    
    # Load from Protobuf
    print(f"📂 Loading from Protobuf: {proto_file}")
    proto_data = ProtobufPersistence.load_snapshot(proto_file)
    print(f"   ✓ Loaded {len(proto_data['customers'])} customer messages")
    print()
    
    print("✅ Demo completed successfully!")
    print()
    print("Next steps:")
    print(f"  1. View JSON file: cat {json_file}")
    print(f"  2. Generate report: python generate_report.py {json_file}")
    print(f"  3. Convert formats: python convert_format.py -i {json_file} -o test.pb --to-proto")
    print()


if __name__ == '__main__':
    import os
    os.makedirs('snapshots', exist_ok=True)
    main()
