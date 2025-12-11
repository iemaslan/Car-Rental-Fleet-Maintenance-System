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
            {'type': n.type, 'recipient': n.recipient}
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
    
    # Advanced Analytics
    print("=" * 70)
    print("📈 ADVANCED ANALYTICS")
    print("=" * 70)
    print()
    
    # 1. Most Profitable Vehicle Class
    print("💰 MOST PROFITABLE VEHICLE CLASS")
    revenue_by_class = defaultdict(float)
    rental_count_by_class = defaultdict(int)
    
    for rental in rentals:
        vehicle_id = rental.get('vehicle_id')
        # Find vehicle class for this rental
        vehicle_class = None
        for vehicle in vehicles:
            if vehicle.get('id') == vehicle_id:
                vehicle_class = vehicle.get('vehicle_class', {}).get('name')
                break
        
        if vehicle_class:
            rental_revenue = sum(item.get('amount', 0) for item in rental.get('charge_items', []))
            revenue_by_class[vehicle_class] += rental_revenue
            rental_count_by_class[vehicle_class] += 1
    
    if revenue_by_class:
        sorted_classes = sorted(revenue_by_class.items(), key=lambda x: x[1], reverse=True)
        print(f"   Top 3 Vehicle Classes by Revenue:")
        for i, (class_name, revenue) in enumerate(sorted_classes[:3], 1):
            count = rental_count_by_class[class_name]
            avg_revenue = revenue / count if count > 0 else 0
            print(f"      {i}. {class_name}: ${revenue:,.2f} ({count} rentals, avg ${avg_revenue:,.2f})")
    else:
        print("   No revenue data available")
    print()
    
    # 2. Customer Loyalty Analysis
    print("🏆 CUSTOMER LOYALTY ANALYSIS")
    customer_spending = defaultdict(float)
    customer_rental_count = defaultdict(int)
    
    for reservation in reservations:
        customer_id = reservation.get('customer_id')
        # Find rentals for this reservation
        for rental in rentals:
            if rental.get('reservation_id') == reservation.get('id'):
                rental_revenue = sum(item.get('amount', 0) for item in rental.get('charge_items', []))
                customer_spending[customer_id] += rental_revenue
                customer_rental_count[customer_id] += 1
    
    if customer_spending:
        sorted_customers = sorted(customer_spending.items(), key=lambda x: x[1], reverse=True)
        print(f"   Top 5 Customers by Total Spending:")
        for i, (customer_id, spending) in enumerate(sorted_customers[:5], 1):
            # Find customer name
            customer_name = "Unknown"
            for customer in customers:
                if customer.get('id') == customer_id:
                    customer_name = customer.get('name', 'Unknown')
                    break
            
            rental_count = customer_rental_count[customer_id]
            avg_spending = spending / rental_count if rental_count > 0 else 0
            print(f"      {i}. {customer_name}: ${spending:,.2f} ({rental_count} rentals, avg ${avg_spending:,.2f})")
    else:
        print("   No customer spending data available")
    print()
    
    # 3. Maintenance Cost Estimates
    print("🔧 MAINTENANCE COST ESTIMATES")
    # Average cost estimates by service type
    maintenance_costs = {
        'OIL_CHANGE': 75.00,
        'TIRE_ROTATION': 50.00,
        'BRAKE_SERVICE': 250.00,
        'INSPECTION': 100.00,
        'ENGINE_REPAIR': 500.00,
        'TRANSMISSION': 800.00,
        'UNKNOWN': 150.00
    }
    
    total_maintenance_cost = 0
    maintenance_cost_by_type = defaultdict(float)
    
    for record in maintenance:
        service_type = record.get('service_type', 'UNKNOWN')
        cost = maintenance_costs.get(service_type, 150.00)
        total_maintenance_cost += cost
        maintenance_cost_by_type[service_type] += cost
    
    print(f"   Estimated Total Maintenance Cost: ${total_maintenance_cost:,.2f}")
    if maintenance:
        print(f"   Average Cost per Maintenance: ${total_maintenance_cost / len(maintenance):,.2f}")
    
    if maintenance_cost_by_type:
        print(f"   Maintenance Costs by Service Type:")
        for service_type, cost in sorted(maintenance_cost_by_type.items(), key=lambda x: x[1], reverse=True):
            count = maintenance_by_type[service_type]
            print(f"      • {service_type}: ${cost:,.2f} ({count} services)")
    print()
    
    # 4. Fleet Utilization Rate
    print("📊 FLEET UTILIZATION")
    if vehicles:
        rented_vehicles = sum(1 for v in vehicles if v.get('status') == 'RENTED')
        available_vehicles = sum(1 for v in vehicles if v.get('status') == 'AVAILABLE')
        utilization_rate = (rented_vehicles / len(vehicles)) * 100
        print(f"   Total Fleet Size: {len(vehicles)}")
        print(f"   Currently Rented: {rented_vehicles}")
        print(f"   Available: {available_vehicles}")
        print(f"   Utilization Rate: {utilization_rate:.1f}%")
    else:
        print("   No fleet data available")
    print()
    
    # 5. Revenue Metrics
    print("💵 REVENUE METRICS")
    if total_rental_revenue > 0:
        print(f"   Total Rental Revenue: ${total_rental_revenue:,.2f}")
        print(f"   Total Maintenance Cost: ${total_maintenance_cost:,.2f}")
        net_revenue = total_rental_revenue - total_maintenance_cost
        profit_margin = (net_revenue / total_rental_revenue) * 100 if total_rental_revenue > 0 else 0
        print(f"   Net Revenue (Est.): ${net_revenue:,.2f}")
        print(f"   Profit Margin (Est.): {profit_margin:.1f}%")
        
        if vehicles:
            revenue_per_vehicle = total_rental_revenue / len(vehicles)
            print(f"   Revenue per Vehicle: ${revenue_per_vehicle:,.2f}")
    else:
        print("   No revenue data available")
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
