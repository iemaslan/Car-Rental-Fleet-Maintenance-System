#!/usr/bin/env python3
"""
Reporting Script for CRFMS.
Loads snapshot data from JSON or Protobuf files and generates aggregate reports.

Usage:
    python generate_report.py snapshot.json
    python generate_report.py snapshot.pb
"""
import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict

from persistence import crfms_pb2


def load_json_snapshot(filename: str) -> dict:
    """Load snapshot from JSON file."""
    with open(filename, 'rt', encoding='utf-8') as f:
        return json.load(f)


def load_proto_snapshot(filename: str) -> dict:
    """Load snapshot from Protobuf file and convert to dict."""
    snapshot = crfms_pb2.CrfmsSnapshot()
    with open(filename, 'rb') as f:
        snapshot.ParseFromString(f.read())
    
    # Convert to dict structure similar to JSON
    data = {
        'metadata': {
            'version': snapshot.metadata.version,
            'timestamp': snapshot.metadata.timestamp,
        },
        'customers': [
            {'id': c.id, 'name': c.name, 'email': c.email}
            for c in snapshot.customers
        ],
        'vehicles': [
            {
                'id': v.id,
                'vehicle_class': {'name': v.vehicle_class.name},
                'status': v.status,
                'odometer': v.odometer.value
            }
            for v in snapshot.vehicles
        ],
        'reservations': [
            {
                'id': r.id,
                'customer_id': r.customer_id,
                'vehicle_class_name': r.vehicle_class_name
            }
            for r in snapshot.reservations
        ],
        'rental_agreements': [
            {
                'id': ra.id,
                'vehicle_id': ra.vehicle_id,
                'actual_return_time': ra.actual_return_time,
                'charge_items': [{'amount': item.amount.amount} for item in ra.charge_items]
            }
            for ra in snapshot.rental_agreements
        ],
        'maintenance_records': [
            {'id': m.id, 'vehicle_id': m.vehicle_id, 'service_type': m.service_type}
            for m in snapshot.maintenance_records
        ],
        'invoices': [
            {
                'id': inv.id,
                'total_amount': inv.total_amount.amount,
                'status': inv.status
            }
            for inv in snapshot.invoices
        ],
        'payments': [
            {
                'id': p.id,
                'amount': p.amount.amount,
                'status': p.status
            }
            for p in snapshot.payments
        ],
        'notifications': [
            {'id': n.id, 'type': n.type, 'sent': n.sent}
            for n in snapshot.notifications
        ]
    }
    
    return data


def generate_report(data: dict) -> None:
    """Generate and print aggregate report from snapshot data."""
    
    print("=" * 70)
    print("CRFMS SYSTEM REPORT")
    print("=" * 70)
    print()
    
    # Metadata
    if 'metadata' in data:
        print(f"Snapshot Version: {data['metadata'].get('version', 'N/A')}")
        print(f"Generated: {data['metadata'].get('timestamp', 'N/A')}")
        print()
    
    # Customer Statistics
    customers = data.get('customers', [])
    print(f"📊 CUSTOMER STATISTICS")
    print(f"   Total Customers: {len(customers)}")
    print()
    
    # Vehicle Statistics
    vehicles = data.get('vehicles', [])
    vehicle_by_class = defaultdict(int)
    vehicle_by_status = defaultdict(int)
    total_mileage = 0
    
    for vehicle in vehicles:
        if 'vehicle_class' in vehicle:
            vehicle_by_class[vehicle['vehicle_class']['name']] += 1
        vehicle_by_status[vehicle.get('status', 'UNKNOWN')] += 1
        total_mileage += vehicle.get('odometer', 0)
    
    print(f"🚗 VEHICLE FLEET STATISTICS")
    print(f"   Total Vehicles: {len(vehicles)}")
    print(f"   Total Fleet Mileage: {total_mileage:,} km")
    if vehicles:
        print(f"   Average Mileage per Vehicle: {total_mileage // len(vehicles):,} km")
    print()
    print("   Vehicles by Class:")
    for class_name, count in sorted(vehicle_by_class.items()):
        print(f"      • {class_name}: {count}")
    print()
    print("   Vehicles by Status:")
    for status, count in sorted(vehicle_by_status.items()):
        print(f"      • {status}: {count}")
    print()
    
    # Reservation Statistics
    reservations = data.get('reservations', [])
    reservations_by_class = defaultdict(int)
    for reservation in reservations:
        reservations_by_class[reservation.get('vehicle_class_name', 'UNKNOWN')] += 1
    
    print(f"📅 RESERVATION STATISTICS")
    print(f"   Total Reservations: {len(reservations)}")
    print("   Reservations by Vehicle Class:")
    for class_name, count in sorted(reservations_by_class.items()):
        print(f"      • {class_name}: {count}")
    print()
    
    # Rental Agreement Statistics
    rentals = data.get('rental_agreements', [])
    active_rentals = sum(1 for r in rentals if not r.get('actual_return_time'))
    completed_rentals = sum(1 for r in rentals if r.get('actual_return_time'))
    total_rental_revenue = sum(
        sum(item.get('amount', 0) for item in r.get('charge_items', []))
        for r in rentals
    )
    
    print(f"🔑 RENTAL AGREEMENT STATISTICS")
    print(f"   Total Rentals: {len(rentals)}")
    print(f"   Active Rentals: {active_rentals}")
    print(f"   Completed Rentals: {completed_rentals}")
    print(f"   Total Revenue from Rentals: ${total_rental_revenue:,.2f}")
    if completed_rentals > 0:
        print(f"   Average Revenue per Completed Rental: ${total_rental_revenue / completed_rentals:,.2f}")
    print()
    
    # Maintenance Statistics
    maintenance = data.get('maintenance_records', [])
    maintenance_by_type = defaultdict(int)
    for record in maintenance:
        maintenance_by_type[record.get('service_type', 'UNKNOWN')] += 1
    
    print(f"🔧 MAINTENANCE STATISTICS")
    print(f"   Total Maintenance Records: {len(maintenance)}")
    print("   Maintenance by Service Type:")
    for service_type, count in sorted(maintenance_by_type.items()):
        print(f"      • {service_type}: {count}")
    print()
    
    # Invoice Statistics
    invoices = data.get('invoices', [])
    invoice_by_status = defaultdict(int)
    total_invoiced = 0
    for invoice in invoices:
        invoice_by_status[invoice.get('status', 'UNKNOWN')] += 1
        total_invoiced += invoice.get('total_amount', 0)
    
    print(f"📄 INVOICE STATISTICS")
    print(f"   Total Invoices: {len(invoices)}")
    print(f"   Total Invoiced Amount: ${total_invoiced:,.2f}")
    if invoices:
        print(f"   Average Invoice Amount: ${total_invoiced / len(invoices):,.2f}")
    print("   Invoices by Status:")
    for status, count in sorted(invoice_by_status.items()):
        print(f"      • {status}: {count}")
    print()
    
    # Payment Statistics
    payments = data.get('payments', [])
    payment_by_status = defaultdict(int)
    total_paid = 0
    for payment in payments:
        payment_by_status[payment.get('status', 'UNKNOWN')] += 1
        total_paid += payment.get('amount', 0)
    
    print(f"💳 PAYMENT STATISTICS")
    print(f"   Total Payments: {len(payments)}")
    print(f"   Total Amount Paid: ${total_paid:,.2f}")
    if payments:
        print(f"   Average Payment Amount: ${total_paid / len(payments):,.2f}")
    print("   Payments by Status:")
    for status, count in sorted(payment_by_status.items()):
        print(f"      • {status}: {count}")
    print()
    
    # Notification Statistics
    notifications = data.get('notifications', [])
    sent_count = sum(1 for n in notifications if n.get('sent'))
    pending_count = len(notifications) - sent_count
    
    print(f"🔔 NOTIFICATION STATISTICS")
    print(f"   Total Notifications: {len(notifications)}")
    print(f"   Sent: {sent_count}")
    print(f"   Pending: {pending_count}")
    print()
    
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description='Generate aggregate report from CRFMS snapshot file',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s snapshot.json
  %(prog)s snapshot.pb
        '''
    )
    
    parser.add_argument('input', help='Input snapshot file (JSON or Protobuf)')
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        print(f"✗ Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Determine file type and load accordingly
        if args.input.endswith('.json'):
            data = load_json_snapshot(args.input)
        elif args.input.endswith('.pb') or args.input.endswith('.protobuf'):
            data = load_proto_snapshot(args.input)
        else:
            # Try JSON first, then Protobuf
            try:
                data = load_json_snapshot(args.input)
            except json.JSONDecodeError:
                data = load_proto_snapshot(args.input)
        
        generate_report(data)
        
    except FileNotFoundError:
        print(f"✗ Error: File not found: {args.input}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"✗ Error: Invalid JSON file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error loading snapshot: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
