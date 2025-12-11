#!/usr/bin/env python3
"""
Minimal demo for HW3 showing JSON and Protobuf file operations.
Creates simple test data to demonstrate serialization formats.
"""
import json
import os
from datetime import datetime
from persistence import crfms_pb2


def demo_json_operations():
    """Demonstrate JSON file operations with context managers."""
    print("=" * 70)
    print("1. JSON FILE OPERATIONS")
    print("=" * 70)
    print()
    
    # Create test data
    snapshot = {
        'metadata': {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'description': 'CRFMS Test Snapshot'
        },
        'customers': [
            {'id': 1, 'name': 'John Doe', 'email': 'john@email.com', 'phone': '+1-555-0101'},
            {'id': 2, 'name': 'Jane Smith', 'email': 'jane@email.com', 'phone': '+1-555-0102'},
        ],
        'vehicles': [
            {
                'id': 1,
                'vehicle_class': {'name': 'SEDAN', 'base_rate': 50.00, 'daily_mileage_allowance': 120},
                'location': {'id': 1, 'name': 'Downtown', 'address': '123 Main St'},
                'status': 'AVAILABLE',
                'odometer': 35000,
                'fuel_level': 'FULL'
            },
            {
                'id': 2,
                'vehicle_class': {'name': 'SUV', 'base_rate': 75.00, 'daily_mileage_allowance': 150},
                'location': {'id': 2, 'name': 'Airport', 'address': '456 Airport Rd'},
                'status': 'RENTED',
                'odometer': 45000,
                'fuel_level': 'THREE_QUARTERS'
            },
        ],
        'rentals': [
            {
                'id': 1,
                'customer_id': 1,
                'vehicle_id': 2,
                'start_odometer': 45000,
                'end_odometer': None,
                'status': 'ACTIVE'
            }
        ]
    }
    
    filename = 'snapshots/test_snapshot.json'
    
    # Save to JSON using context manager (wt mode)
    print(f"💾 Saving to JSON file: {filename}")
    with open(filename, mode='wt', encoding='utf-8') as f:
        json.dump(snapshot, f, indent=2, ensure_ascii=False)
    print(f"   ✓ File saved successfully")
    print()
    
    # Load from JSON using context manager (rt mode)
    print(f"📂 Loading from JSON file: {filename}")
    try:
        with open(filename, mode='rt', encoding='utf-8') as f:
            loaded_data = json.load(f)
        print(f"   ✓ Loaded {len(loaded_data['customers'])} customers")
        print(f"   ✓ Loaded {len(loaded_data['vehicles'])} vehicles")
        print(f"   ✓ Loaded {len(loaded_data['rentals'])} rentals")
    except FileNotFoundError:
        print(f"   ✗ Error: File not found")
    except json.JSONDecodeError as e:
        print(f"   ✗ Error: Malformed JSON - {e}")
    print()
    
    return snapshot


def demo_protobuf_operations(json_data):
    """Demonstrate Protocol Buffers file operations."""
    print("=" * 70)
    print("2. PROTOCOL BUFFERS OPERATIONS")
    print("=" * 70)
    print()
    
    # Create protobuf snapshot
    snapshot = crfms_pb2.CrfmsSnapshot()
    
    # Set metadata
    snapshot.metadata.version = json_data['metadata']['version']
    snapshot.metadata.timestamp = json_data['metadata']['timestamp']
    snapshot.metadata.description = json_data['metadata']['description']
    
    # Add customers
    for cust in json_data['customers']:
        customer = snapshot.customers.add()
        customer.id = cust['id']
        customer.name = cust['name']
        customer.email = cust['email']
        customer.phone = cust['phone']
    
    # Add vehicles
    for veh in json_data['vehicles']:
        vehicle = snapshot.vehicles.add()
        vehicle.id = veh['id']
        vehicle.vehicle_class.name = veh['vehicle_class']['name']
        vehicle.vehicle_class.base_rate.amount = veh['vehicle_class']['base_rate']
        vehicle.vehicle_class.base_rate.currency = "USD"
        vehicle.vehicle_class.daily_mileage_allowance = veh['vehicle_class']['daily_mileage_allowance']
        vehicle.location.id = veh['location']['id']
        vehicle.location.name = veh['location']['name']
        vehicle.location.address = veh['location']['address']
        vehicle.status = veh['status']
        vehicle.odometer.value = veh['odometer']
        vehicle.fuel_level.level = veh['fuel_level']
    
    filename = 'snapshots/test_snapshot.pb'
    
    # Save to Protobuf using context manager (wb mode)
    print(f"💾 Saving to Protobuf file: {filename}")
    with open(filename, mode='wb') as f:
        f.write(snapshot.SerializeToString())
    print(f"   ✓ File saved successfully ({len(snapshot.SerializeToString())} bytes)")
    print()
    
    # Load from Protobuf using context manager (rb mode)
    print(f"📂 Loading from Protobuf file: {filename}")
    try:
        loaded_snapshot = crfms_pb2.CrfmsSnapshot()
        with open(filename, mode='rb') as f:
            loaded_snapshot.ParseFromString(f.read())
        print(f"   ✓ Loaded {len(loaded_snapshot.customers)} customers")
        print(f"   ✓ Loaded {len(loaded_snapshot.vehicles)} vehicles")
    except FileNotFoundError:
        print(f"   ✗ Error: File not found")
    print()


def demo_error_handling():
    """Demonstrate error handling for file operations."""
    print("=" * 70)
    print("3. ERROR HANDLING DEMONSTRATION")
    print("=" * 70)
    print()
    
    # Test missing file
    print("📂 Attempting to load non-existent file...")
    try:
        with open('nonexistent.json', mode='rt') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("   ✓ Caught FileNotFoundError correctly")
    print()
    
    # Test malformed JSON
    print("📂 Attempting to load malformed JSON...")
    malformed_file = 'snapshots/malformed.json'
    with open(malformed_file, mode='wt') as f:
        f.write('{invalid json content')
    
    try:
        with open(malformed_file, mode='rt') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"   ✓ Caught JSONDecodeError: {e.msg}")
    print()


def demo_comparison():
    """Compare JSON and Protobuf file sizes."""
    print("=" * 70)
    print("4. FORMAT COMPARISON")
    print("=" * 70)
    print()
    
    json_file = 'snapshots/test_snapshot.json'
    proto_file = 'snapshots/test_snapshot.pb'
    
    json_size = os.path.getsize(json_file)
    proto_size = os.path.getsize(proto_file)
    
    print(f"File Size Comparison:")
    print(f"   JSON:     {json_size:,} bytes")
    print(f"   Protobuf: {proto_size:,} bytes")
    print(f"   Savings:  {json_size - proto_size:,} bytes ({(1 - proto_size/json_size)*100:.1f}% smaller)")
    print()
    
    print(f"Characteristics:")
    print(f"   JSON:     Human-readable, text-based, UTF-8 encoding")
    print(f"   Protobuf: Binary format, compact, requires schema")
    print()


def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "HW3: File Operations & Protocol Buffers" + " " * 14 + "║")
    print("║" + " " * 23 + "Demonstration Script" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    # Create snapshots directory
    os.makedirs('snapshots', exist_ok=True)
    
    # Run demonstrations
    json_data = demo_json_operations()
    demo_protobuf_operations(json_data)
    demo_error_handling()
    demo_comparison()
    
    print("=" * 70)
    print("✅ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
    print("=" * 70)
    print()
    print("Files created:")
    print("  • snapshots/test_snapshot.json  (JSON format)")
    print("  • snapshots/test_snapshot.pb    (Protobuf format)")
    print()
    print("Try these commands:")
    print("  • cat snapshots/test_snapshot.json")
    print("  • python generate_report.py snapshots/test_snapshot.json")
    print("  • python convert_format.py -i snapshots/test_snapshot.json -o test.pb --to-proto")
    print()


if __name__ == '__main__':
    main()
