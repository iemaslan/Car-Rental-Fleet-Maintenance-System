#!/usr/bin/env python3
"""
Conversion Utility for CRFMS Persistence Formats.
Converts between JSON and Protocol Buffers snapshot files.

Usage:
    python convert_format.py --input snapshot.json --output snapshot.pb --to-proto
    python convert_format.py --input snapshot.pb --output snapshot.json --to-json
"""
import argparse
import json
import sys
from pathlib import Path

from persistence import crfms_pb2

# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def colored_print(message: str, color: str = Colors.ENDC) -> None:
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.ENDC}")


def json_to_proto(json_file: str, proto_file: str) -> None:
    """Convert JSON snapshot to Protocol Buffers format."""
    colored_print(f"\n🔄 Converting {json_file} (JSON) → {proto_file} (Protobuf)...", Colors.OKCYAN)
    
    try:
        # Load JSON
        with open(json_file, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create protobuf snapshot
        snapshot = crfms_pb2.CrfmsSnapshot()
        
        # Metadata
        if 'metadata' in data:
            snapshot.metadata.version = data['metadata'].get('version', '1.0')
            snapshot.metadata.timestamp = data['metadata'].get('timestamp', '')
            snapshot.metadata.description = data['metadata'].get('description', '')
        
        # Customers
        for cust_data in data.get('customers', []):
            customer = snapshot.customers.add()
            customer.id = cust_data['id']
            customer.name = cust_data['name']
            customer.email = cust_data['email']
            customer.phone = cust_data['phone']
        
        # Vehicles
        for veh_data in data.get('vehicles', []):
            vehicle = snapshot.vehicles.add()
            vehicle.id = veh_data['id']
            vehicle.vehicle_class.name = veh_data['vehicle_class']['name']
            vehicle.vehicle_class.base_rate.amount = veh_data['vehicle_class']['base_rate']
            vehicle.vehicle_class.base_rate.currency = "USD"
            vehicle.vehicle_class.daily_mileage_allowance = veh_data['vehicle_class']['daily_mileage_allowance']
            vehicle.location.id = veh_data['location']['id']
            vehicle.location.name = veh_data['location']['name']
            vehicle.location.address = veh_data['location']['address']
            vehicle.status = veh_data['status']
            vehicle.odometer.value = veh_data['odometer']
            vehicle.fuel_level.level = veh_data['fuel_level']
        
        # Reservations
        for res_data in data.get('reservations', []):
            reservation = snapshot.reservations.add()
            reservation.id = res_data['id']
            reservation.customer_id = res_data['customer_id']
            reservation.vehicle_class_name = res_data['vehicle_class_name']
            reservation.location_id = res_data['location_id']
            reservation.pickup_time = res_data['pickup_time']
            reservation.return_time = res_data['return_time']
            reservation.addons.extend(res_data.get('addons', []))
            reservation.insurance_tier = res_data['insurance_tier']
        
        # Rental Agreements
        for rental_data in data.get('rental_agreements', []):
            rental = snapshot.rental_agreements.add()
            rental.id = rental_data['id']
            rental.reservation_id = rental_data['reservation_id']
            rental.vehicle_id = rental_data['vehicle_id']
            rental.pickup_token = rental_data['pickup_token']
            rental.start_odometer.value = rental_data['start_odometer']
            if rental_data.get('end_odometer'):
                rental.end_odometer.value = rental_data['end_odometer']
            rental.start_fuel_level.level = rental_data['start_fuel_level']
            if rental_data.get('end_fuel_level'):
                rental.end_fuel_level.level = rental_data['end_fuel_level']
            rental.pickup_time = rental_data['pickup_time']
            rental.expected_return_time = rental_data['expected_return_time']
            if rental_data.get('actual_return_time'):
                rental.actual_return_time = rental_data['actual_return_time']
            for item in rental_data.get('charge_items', []):
                charge = rental.charge_items.add()
                charge.description = item['description']
                charge.amount.amount = item['amount']
                charge.amount.currency = "USD"
        
        # Maintenance Records
        for maint_data in data.get('maintenance_records', []):
            record = snapshot.maintenance_records.add()
            record.id = maint_data['id']
            record.vehicle_id = maint_data['vehicle_id']
            record.service_type = maint_data['service_type']
            record.odometer_threshold.value = maint_data['odometer_threshold']
            if maint_data.get('time_threshold'):
                record.time_threshold = maint_data['time_threshold']
            if maint_data.get('last_service_date'):
                record.last_service_date = maint_data['last_service_date']
            if maint_data.get('last_service_odometer'):
                record.last_service_odometer.value = maint_data['last_service_odometer']
        
        # Invoices
        for inv_data in data.get('invoices', []):
            invoice = snapshot.invoices.add()
            invoice.id = inv_data['id']
            invoice.rental_agreement_id = inv_data['rental_agreement_id']
            for item in inv_data.get('charge_items', []):
                charge = invoice.charge_items.add()
                charge.description = item['description']
                charge.amount.amount = item['amount']
                charge.amount.currency = "USD"
            invoice.total_amount.amount = inv_data['total_amount']
            invoice.total_amount.currency = "USD"
            invoice.status = inv_data['status']
            invoice.created_at = inv_data['created_at']
        
        # Payments
        for pay_data in data.get('payments', []):
            payment = snapshot.payments.add()
            payment.id = pay_data['id']
            payment.invoice_id = pay_data['invoice_id']
            payment.amount.amount = pay_data['amount']
            payment.amount.currency = "USD"
            payment.payment_method = pay_data['payment_method']
            payment.transaction_id = pay_data['transaction_id']
            payment.status = pay_data['status']
            payment.timestamp = pay_data['timestamp']
        
        # Notifications
        for notif_data in data.get('notifications', []):
            notification = snapshot.notifications.add()
            notification.id = notif_data['id']
            notification.recipient = notif_data['recipient']
            notification.type = notif_data['type']
            notification.message = notif_data['message']
            notification.timestamp = notif_data['timestamp']
            notification.sent = notif_data['sent']
        
        # Audit Entries
        for audit_data in data.get('audit_entries', []):
            entry = snapshot.audit_entries.add()
            entry.id = audit_data['id']
            entry.timestamp = audit_data['timestamp']
            entry.event_type = audit_data['event_type']
            entry.actor_type = audit_data['actor_type']
            entry.actor_id = audit_data['actor_id']
            entry.actor_name = audit_data['actor_name']
            entry.entity_type = audit_data['entity_type']
            entry.entity_id = audit_data['entity_id']
            entry.description = audit_data['description']
            if 'metadata' in audit_data:
                for key, value in audit_data['metadata'].items():
                    entry.metadata[key] = str(value)
        
        # Write protobuf
        with open(proto_file, 'wb') as f:
            f.write(snapshot.SerializeToString())
        
        # Get file sizes
        json_size = Path(json_file).stat().st_size
        proto_size = Path(proto_file).stat().st_size
        savings = ((json_size - proto_size) / json_size * 100) if json_size > 0 else 0
        
        colored_print(f"✓ Successfully converted to Protobuf", Colors.OKGREEN)
        colored_print(f"  JSON size:  {json_size:,} bytes", Colors.ENDC)
        colored_print(f"  Proto size: {proto_size:,} bytes", Colors.ENDC)
        colored_print(f"  Savings:    {savings:.1f}%", Colors.OKGREEN)
        
    except FileNotFoundError:
        colored_print(f"✗ Error: Input file '{json_file}' not found", Colors.FAIL)
        sys.exit(1)
    except json.JSONDecodeError as e:
        colored_print(f"✗ Error: Invalid JSON file: {e}", Colors.FAIL)
        sys.exit(1)
    except Exception as e:
        colored_print(f"✗ Error during conversion: {e}", Colors.FAIL)
        sys.exit(1)


def proto_to_json(proto_file: str, json_file: str) -> None:
    """Convert Protocol Buffers snapshot to JSON format."""
    colored_print(f"\n🔄 Converting {proto_file} (Protobuf) → {json_file} (JSON)...", Colors.OKCYAN)
    
    try:
        # Load protobuf
        snapshot = crfms_pb2.CrfmsSnapshot()
        with open(proto_file, 'rb') as f:
            snapshot.ParseFromString(f.read())
        
        # Build JSON structure
        data = {
            'metadata': {
                'version': snapshot.metadata.version,
                'timestamp': snapshot.metadata.timestamp,
                'description': snapshot.metadata.description
            },
            'customers': [],
            'vehicles': [],
            'reservations': [],
            'rental_agreements': [],
            'maintenance_records': [],
            'invoices': [],
            'payments': [],
            'notifications': [],
            'audit_entries': []
        }
        
        # Customers
        for customer in snapshot.customers:
            data['customers'].append({
                'id': customer.id,
                'name': customer.name,
                'email': customer.email,
                'phone': customer.phone
            })
        
        # Vehicles
        for vehicle in snapshot.vehicles:
            data['vehicles'].append({
                'id': vehicle.id,
                'vehicle_class': {
                    'name': vehicle.vehicle_class.name,
                    'base_rate': vehicle.vehicle_class.base_rate.amount,
                    'daily_mileage_allowance': vehicle.vehicle_class.daily_mileage_allowance
                },
                'location': {
                    'id': vehicle.location.id,
                    'name': vehicle.location.name,
                    'address': vehicle.location.address
                },
                'status': vehicle.status,
                'odometer': vehicle.odometer.value,
                'fuel_level': vehicle.fuel_level.level
            })
        
        # Reservations
        for reservation in snapshot.reservations:
            data['reservations'].append({
                'id': reservation.id,
                'customer_id': reservation.customer_id,
                'vehicle_class_name': reservation.vehicle_class_name,
                'location_id': reservation.location_id,
                'pickup_time': reservation.pickup_time,
                'return_time': reservation.return_time,
                'addons': list(reservation.addons),
                'insurance_tier': reservation.insurance_tier
            })
        
        # Rental Agreements
        for rental in snapshot.rental_agreements:
            rental_dict = {
                'id': rental.id,
                'reservation_id': rental.reservation_id,
                'vehicle_id': rental.vehicle_id,
                'pickup_token': rental.pickup_token,
                'start_odometer': rental.start_odometer.value,
                'end_odometer': rental.end_odometer.value if rental.HasField('end_odometer') else None,
                'start_fuel_level': rental.start_fuel_level.level,
                'end_fuel_level': rental.end_fuel_level.level if rental.HasField('end_fuel_level') else None,
                'pickup_time': rental.pickup_time,
                'expected_return_time': rental.expected_return_time,
                'actual_return_time': rental.actual_return_time if rental.actual_return_time else None,
                'charge_items': [
                    {'description': item.description, 'amount': item.amount.amount}
                    for item in rental.charge_items
                ]
            }
            data['rental_agreements'].append(rental_dict)
        
        # Maintenance Records
        for record in snapshot.maintenance_records:
            maint_dict = {
                'id': record.id,
                'vehicle_id': record.vehicle_id,
                'service_type': record.service_type,
                'odometer_threshold': record.odometer_threshold.value,
                'time_threshold': record.time_threshold if record.time_threshold else None,
                'last_service_date': record.last_service_date if record.last_service_date else None,
                'last_service_odometer': record.last_service_odometer.value if record.HasField('last_service_odometer') else None
            }
            data['maintenance_records'].append(maint_dict)
        
        # Invoices
        for invoice in snapshot.invoices:
            data['invoices'].append({
                'id': invoice.id,
                'rental_agreement_id': invoice.rental_agreement_id,
                'charge_items': [
                    {'description': item.description, 'amount': item.amount.amount}
                    for item in invoice.charge_items
                ],
                'total_amount': invoice.total_amount.amount,
                'status': invoice.status,
                'created_at': invoice.created_at
            })
        
        # Payments
        for payment in snapshot.payments:
            data['payments'].append({
                'id': payment.id,
                'invoice_id': payment.invoice_id,
                'amount': payment.amount.amount,
                'payment_method': payment.payment_method,
                'transaction_id': payment.transaction_id,
                'status': payment.status,
                'timestamp': payment.timestamp
            })
        
        # Notifications
        for notification in snapshot.notifications:
            data['notifications'].append({
                'id': notification.id,
                'recipient': notification.recipient,
                'type': notification.type,
                'message': notification.message,
                'timestamp': notification.timestamp,
                'sent': notification.sent
            })
        
        # Audit Entries
        for entry in snapshot.audit_entries:
            data['audit_entries'].append({
                'id': entry.id,
                'timestamp': entry.timestamp,
                'event_type': entry.event_type,
                'actor_type': entry.actor_type,
                'actor_id': entry.actor_id,
                'actor_name': entry.actor_name,
                'entity_type': entry.entity_type,
                'entity_id': entry.entity_id,
                'description': entry.description,
                'metadata': dict(entry.metadata)
            })
        
        # Write JSON
        with open(json_file, 'wt', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Get file sizes
        proto_size = Path(proto_file).stat().st_size
        json_size = Path(json_file).stat().st_size
        expansion = ((json_size - proto_size) / proto_size * 100) if proto_size > 0 else 0
        
        colored_print(f"✓ Successfully converted to JSON", Colors.OKGREEN)
        colored_print(f"  Proto size: {proto_size:,} bytes", Colors.ENDC)
        colored_print(f"  JSON size:  {json_size:,} bytes", Colors.ENDC)
        colored_print(f"  Expansion:  {expansion:.1f}%", Colors.WARNING)
        
    except FileNotFoundError:
        colored_print(f"✗ Error: Input file '{proto_file}' not found", Colors.FAIL)
        sys.exit(1)
    except Exception as e:
        colored_print(f"✗ Error during conversion: {e}", Colors.FAIL)
        sys.exit(1)


def main():
    colored_print("\n" + "="*70, Colors.BOLD)
    colored_print("  CRFMS Format Converter - JSON ↔ Protocol Buffers", Colors.HEADER + Colors.BOLD)
    colored_print("="*70 + "\n", Colors.BOLD)
    
    parser = argparse.ArgumentParser(
        description='Convert CRFMS snapshots between JSON and Protocol Buffers formats',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s --input snapshot.json --output snapshot.pb --to-proto
  %(prog)s --input snapshot.pb --output snapshot.json --to-json
        '''
    )
    
    parser.add_argument('--input', '-i', required=True, help='Input file path')
    parser.add_argument('--output', '-o', required=True, help='Output file path')
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--to-proto', action='store_true', help='Convert JSON to Protobuf')
    group.add_argument('--to-json', action='store_true', help='Convert Protobuf to JSON')
    
    args = parser.parse_args()
    
    if args.to_proto:
        json_to_proto(args.input, args.output)
    else:
        proto_to_json(args.input, args.output)
    
    colored_print("\n" + "="*70, Colors.BOLD)
    colored_print("  Conversion completed successfully! ✨", Colors.OKGREEN + Colors.BOLD)
    colored_print("="*70 + "\n", Colors.BOLD)


if __name__ == '__main__':
    main()
