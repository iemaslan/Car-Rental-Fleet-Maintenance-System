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
    
    # Create test data - COMPREHENSIVE DATASET
    now = datetime.now().isoformat()
    snapshot = {
        'metadata': {
            'version': '1.0',
            'timestamp': now,
            'description': 'CRFMS Test Snapshot - Comprehensive Dataset with 10+ Entities Each'
        },
        'customers': [
            {'id': 1, 'name': 'İrem Aslan', 'email': 'irem.aslan@email.com', 'phone': '+90-555-0101'},
            {'id': 2, 'name': 'Can Somer', 'email': 'can.somer@email.com', 'phone': '+90-555-0102'},
            {'id': 3, 'name': 'Beyza Aslan', 'email': 'beyza.aslan@email.com', 'phone': '+90-555-0103'},
            {'id': 4, 'name': 'Güney Ulusoy', 'email': 'guney.ulusoy@email.com', 'phone': '+90-555-0104'},
            {'id': 5, 'name': 'Gaye Şeker', 'email': 'gaye.seker@email.com', 'phone': '+90-555-0105'},
            {'id': 6, 'name': 'Berk Özköylü', 'email': 'berk.ozkoylu@email.com', 'phone': '+90-555-0106'},
            {'id': 7, 'name': 'Muhsin Yılmaz', 'email': 'muhsin.yilmaz@email.com', 'phone': '+90-555-0107'},
            {'id': 8, 'name': 'Ada Ergen', 'email': 'ada.ergen@email.com', 'phone': '+90-555-0108'},
            {'id': 9, 'name': 'Ece Kaya', 'email': 'ece.kaya@email.com', 'phone': '+90-555-0109'},
            {'id': 10, 'name': 'Ahmet Demir', 'email': 'ahmet.demir@email.com', 'phone': '+90-555-0110'},
            {'id': 11, 'name': 'Zeynep Yıldız', 'email': 'zeynep.yildiz@email.com', 'phone': '+90-555-0111'},
            {'id': 12, 'name': 'Mert Çelik', 'email': 'mert.celik@email.com', 'phone': '+90-555-0112'},
            {'id': 13, 'name': 'Binnur Kurt', 'email': 'binnur.kurt@email.com', 'phone': '+90-555-0113'},
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
            {
                'id': 3,
                'vehicle_class': {'name': 'COMPACT', 'base_rate': 30.00, 'daily_mileage_allowance': 100},
                'location': {'id': 1, 'name': 'Downtown', 'address': '123 Main St'},
                'status': 'RENTED',
                'odometer': 25000,
                'fuel_level': 'HALF'
            },
            {
                'id': 4,
                'vehicle_class': {'name': 'MASERATI GHIBLI', 'base_rate': 450.00, 'daily_mileage_allowance': 250},
                'location': {'id': 3, 'name': 'City Center', 'address': '789 Central Ave'},
                'status': 'AVAILABLE',
                'odometer': 8000,
                'fuel_level': 'FULL'
            },
            {
                'id': 5,
                'vehicle_class': {'name': 'VAN', 'base_rate': 90.00, 'daily_mileage_allowance': 180},
                'location': {'id': 2, 'name': 'Airport', 'address': '456 Airport Rd'},
                'status': 'AVAILABLE',
                'odometer': 55000,
                'fuel_level': 'HALF'
            },
            {
                'id': 6,
                'vehicle_class': {'name': 'FERRARI 488', 'base_rate': 850.00, 'daily_mileage_allowance': 200},
                'location': {'id': 1, 'name': 'Downtown', 'address': '123 Main St'},
                'status': 'MAINTENANCE',
                'odometer': 5000,
                'fuel_level': 'FULL'
            },
            {
                'id': 7,
                'vehicle_class': {'name': 'COMPACT', 'base_rate': 30.00, 'daily_mileage_allowance': 100},
                'location': {'id': 3, 'name': 'City Center', 'address': '789 Central Ave'},
                'status': 'AVAILABLE',
                'odometer': 12000,
                'fuel_level': 'FULL'
            },
            {
                'id': 8,
                'vehicle_class': {'name': 'ROLLS ROYCE GHOST', 'base_rate': 1200.00, 'daily_mileage_allowance': 150},
                'location': {'id': 1, 'name': 'Downtown', 'address': '123 Main St'},
                'status': 'RENTED',
                'odometer': 3500,
                'fuel_level': 'FULL'
            },
            {
                'id': 9,
                'vehicle_class': {'name': 'LAMBORGHINI URUS', 'base_rate': 950.00, 'daily_mileage_allowance': 200},
                'location': {'id': 2, 'name': 'Airport', 'address': '456 Airport Rd'},
                'status': 'RENTED',
                'odometer': 6200,
                'fuel_level': 'THREE_QUARTERS'
            },
            {
                'id': 10,
                'vehicle_class': {'name': 'VAN', 'base_rate': 90.00, 'daily_mileage_allowance': 180},
                'location': {'id': 3, 'name': 'City Center', 'address': '789 Central Ave'},
                'status': 'AVAILABLE',
                'odometer': 41000,
                'fuel_level': 'FULL'
            },
            {
                'id': 11,
                'vehicle_class': {'name': 'BENTLEY CONTINENTAL', 'base_rate': 750.00, 'daily_mileage_allowance': 180},
                'location': {'id': 2, 'name': 'Airport', 'address': '456 Airport Rd'},
                'status': 'AVAILABLE',
                'odometer': 9500,
                'fuel_level': 'FULL'
            },
            {
                'id': 12,
                'vehicle_class': {'name': 'PORSCHE 911', 'base_rate': 650.00, 'daily_mileage_allowance': 220},
                'location': {'id': 1, 'name': 'Downtown', 'address': '123 Main St'},
                'status': 'AVAILABLE',
                'odometer': 12000,
                'fuel_level': 'FULL'
            },
            {
                'id': 13,
                'vehicle_class': {'name': 'MAYBACH S680', 'base_rate': 1500.00, 'daily_mileage_allowance': 150},
                'location': {'id': 3, 'name': 'City Center', 'address': '789 Central Ave'},
                'status': 'RENTED',
                'odometer': 2500,
                'fuel_level': 'FULL'
            },
        ],
        'reservations': [
            {
                'id': 1,
                'customer_id': 1,
                'vehicle_class_name': 'ROLLS ROYCE GHOST',
                'location_id': 1,
                'pickup_time': now,
                'return_time': '2025-12-15T10:00:00'
            },
            {
                'id': 2,
                'customer_id': 2,
                'vehicle_class_name': 'MASERATI GHIBLI',
                'location_id': 3,
                'pickup_time': '2025-12-12T14:00:00',
                'return_time': '2025-12-14T14:00:00'
            },
            {
                'id': 3,
                'customer_id': 3,
                'vehicle_class_name': 'COMPACT',
                'location_id': 1,
                'pickup_time': '2025-12-13T09:00:00',
                'return_time': '2025-12-16T09:00:00'
            },
            {
                'id': 4,
                'customer_id': 4,
                'vehicle_class_name': 'LAMBORGHINI URUS',
                'location_id': 2,
                'pickup_time': '2025-12-14T11:00:00',
                'return_time': '2025-12-18T11:00:00'
            },
            {
                'id': 5,
                'customer_id': 5,
                'vehicle_class_name': 'VAN',
                'location_id': 2,
                'pickup_time': '2025-12-15T08:00:00',
                'return_time': '2025-12-20T08:00:00'
            },
            {
                'id': 6,
                'customer_id': 6,
                'vehicle_class_name': 'BENTLEY CONTINENTAL',
                'location_id': 2,
                'pickup_time': '2025-12-16T13:00:00',
                'return_time': '2025-12-19T13:00:00'
            },
            {
                'id': 7,
                'customer_id': 7,
                'vehicle_class_name': 'SEDAN',
                'location_id': 1,
                'pickup_time': '2025-12-17T10:00:00',
                'return_time': '2025-12-21T10:00:00'
            },
            {
                'id': 8,
                'customer_id': 8,
                'vehicle_class_name': 'PORSCHE 911',
                'location_id': 1,
                'pickup_time': '2025-12-18T09:00:00',
                'return_time': '2025-12-22T09:00:00'
            },
            {
                'id': 9,
                'customer_id': 9,
                'vehicle_class_name': 'FERRARI 488',
                'location_id': 1,
                'pickup_time': '2025-12-19T15:00:00',
                'return_time': '2025-12-24T15:00:00'
            },
            {
                'id': 10,
                'customer_id': 10,
                'vehicle_class_name': 'VAN',
                'location_id': 1,
                'pickup_time': '2025-12-20T12:00:00',
                'return_time': '2025-12-25T12:00:00'
            },
            {
                'id': 11,
                'customer_id': 13,
                'vehicle_class_name': 'MAYBACH S680',
                'location_id': 3,
                'pickup_time': '2025-12-13T15:00:00',
                'return_time': '2025-12-17T15:00:00'
            },
        ],
        'rental_agreements': [
            {
                'id': 1,
                'reservation_id': 1,
                'vehicle_id': 2,
                'pickup_token': 'TOKEN123',
                'start_odometer': 45000,
                'end_odometer': None,
                'start_fuel_level': 'FULL',
                'end_fuel_level': None,
                'pickup_time': now,
                'expected_return_time': '2025-12-15T10:00:00',
                'actual_return_time': None,
                'charge_items': [
                    {'description': 'Base Rental (4 days)', 'amount': 300.00},
                    {'description': 'GPS', 'amount': 40.00}
                ]
            },
            {
                'id': 2,
                'reservation_id': 3,
                'vehicle_id': 3,
                'pickup_token': 'TOKEN456',
                'start_odometer': 25000,
                'end_odometer': 25450,
                'start_fuel_level': 'FULL',
                'end_fuel_level': 'HALF',
                'pickup_time': '2025-12-09T09:00:00',
                'expected_return_time': '2025-12-11T09:00:00',
                'actual_return_time': '2025-12-11T10:30:00',
                'charge_items': [
                    {'description': 'Base Rental (2 days)', 'amount': 60.00},
                    {'description': 'Fuel Charge', 'amount': 25.00},
                    {'description': 'Late Return', 'amount': 15.00}
                ]
            },
            {
                'id': 3,
                'reservation_id': 4,
                'vehicle_id': 9,
                'pickup_token': 'TOKEN789',
                'start_odometer': 6200,
                'end_odometer': None,
                'start_fuel_level': 'FULL',
                'end_fuel_level': None,
                'pickup_time': '2025-12-14T11:00:00',
                'expected_return_time': '2025-12-18T11:00:00',
                'actual_return_time': None,
                'charge_items': [
                    {'description': 'Lamborghini Urus Rental (4 days)', 'amount': 3800.00},
                    {'description': 'Premium Insurance', 'amount': 320.00}
                ]
            },
            {
                'id': 4,
                'reservation_id': 1,
                'vehicle_id': 8,
                'pickup_token': 'TOKEN321',
                'start_odometer': 3500,
                'end_odometer': None,
                'start_fuel_level': 'FULL',
                'end_fuel_level': None,
                'pickup_time': now,
                'expected_return_time': '2025-12-15T10:00:00',
                'actual_return_time': None,
                'charge_items': [
                    {'description': 'Rolls Royce Ghost Rental (3 days)', 'amount': 3600.00},
                    {'description': 'Chauffeur Service', 'amount': 450.00}
                ]
            },
            {
                'id': 5,
                'reservation_id': 5,
                'vehicle_id': 5,
                'pickup_token': 'TOKEN654',
                'start_odometer': 55000,
                'end_odometer': 55890,
                'start_fuel_level': 'FULL',
                'end_fuel_level': 'QUARTER',
                'pickup_time': '2025-12-08T08:00:00',
                'expected_return_time': '2025-12-11T08:00:00',
                'actual_return_time': '2025-12-11T20:00:00',
                'charge_items': [
                    {'description': 'Base Rental (3 days)', 'amount': 270.00},
                    {'description': 'Extra Driver', 'amount': 45.00},
                    {'description': 'Fuel Charge', 'amount': 45.00},
                    {'description': 'Late Return', 'amount': 30.00}
                ]
            },
            {
                'id': 6,
                'reservation_id': 11,
                'vehicle_id': 13,
                'pickup_token': 'VIPTOKEN999',
                'start_odometer': 2500,
                'end_odometer': None,
                'start_fuel_level': 'FULL',
                'end_fuel_level': None,
                'pickup_time': '2025-12-13T15:00:00',
                'expected_return_time': '2025-12-17T15:00:00',
                'actual_return_time': None,
                'charge_items': [
                    {'description': 'Maybach S680 VIP Limousine Rental (4 days)', 'amount': 6000.00},
                    {'description': 'Premium Chauffeur Service', 'amount': 800.00},
                    {'description': 'Airport VIP Transfer', 'amount': 350.00},
                    {'description': 'Premium Insurance', 'amount': 400.00}
                ]
            },
        ],
        'maintenance_records': [
            {
                'id': 1,
                'vehicle_id': 1,
                'service_type': 'OIL_CHANGE',
                'odometer_threshold': 40000,
                'time_threshold': '2025-12-20T00:00:00',
                'last_service_date': '2025-09-15T10:00:00',
                'last_service_odometer': 30000
            },
            {
                'id': 2,
                'vehicle_id': 2,
                'service_type': 'TIRE_ROTATION',
                'odometer_threshold': 50000,
                'time_threshold': None,
                'last_service_date': '2025-10-01T14:00:00',
                'last_service_odometer': 40000
            },
            {
                'id': 3,
                'vehicle_id': 3,
                'service_type': 'INSPECTION',
                'odometer_threshold': 30000,
                'time_threshold': '2025-12-25T00:00:00',
                'last_service_date': '2025-08-10T11:00:00',
                'last_service_odometer': 20000
            },
            {
                'id': 4,
                'vehicle_id': 4,
                'service_type': 'BRAKE_SERVICE',
                'odometer_threshold': 20000,
                'time_threshold': '2026-01-15T00:00:00',
                'last_service_date': '2025-11-01T09:00:00',
                'last_service_odometer': 12000
            },
            {
                'id': 5,
                'vehicle_id': 5,
                'service_type': 'OIL_CHANGE',
                'odometer_threshold': 60000,
                'time_threshold': '2025-12-28T00:00:00',
                'last_service_date': '2025-09-20T13:00:00',
                'last_service_odometer': 50000
            },
            {
                'id': 6,
                'vehicle_id': 6,
                'service_type': 'MAJOR_SERVICE',
                'odometer_threshold': 80000,
                'time_threshold': None,
                'last_service_date': '2025-10-15T10:00:00',
                'last_service_odometer': 75000
            },
            {
                'id': 7,
                'vehicle_id': 7,
                'service_type': 'INSPECTION',
                'odometer_threshold': 15000,
                'time_threshold': '2026-02-01T00:00:00',
                'last_service_date': '2025-11-10T11:00:00',
                'last_service_odometer': 10000
            },
            {
                'id': 8,
                'vehicle_id': 8,
                'service_type': 'TIRE_ROTATION',
                'odometer_threshold': 70000,
                'time_threshold': None,
                'last_service_date': '2025-09-25T14:00:00',
                'last_service_odometer': 58000
            },
            {
                'id': 9,
                'vehicle_id': 9,
                'service_type': 'OIL_CHANGE',
                'odometer_threshold': 33000,
                'time_threshold': '2026-01-05T00:00:00',
                'last_service_date': '2025-10-20T10:00:00',
                'last_service_odometer': 25000
            },
            {
                'id': 10,
                'vehicle_id': 10,
                'service_type': 'BRAKE_SERVICE',
                'odometer_threshold': 46000,
                'time_threshold': '2025-12-30T00:00:00',
                'last_service_date': '2025-11-05T15:00:00',
                'last_service_odometer': 39000
            },
        ],
        'invoices': [
            {
                'id': 1,
                'rental_agreement_id': 2,
                'charge_items': [
                    {'description': 'Base Rental (2 days)', 'amount': 60.00},
                    {'description': 'Fuel Charge', 'amount': 25.00},
                    {'description': 'Late Return', 'amount': 15.00}
                ],
                'total_amount': 100.00,
                'status': 'PAID',
                'created_at': '2025-12-11T11:00:00'
            },
            {
                'id': 2,
                'rental_agreement_id': 1,
                'charge_items': [
                    {'description': 'Base Rental (4 days)', 'amount': 300.00},
                    {'description': 'GPS', 'amount': 40.00}
                ],
                'total_amount': 340.00,
                'status': 'PENDING',
                'created_at': now
            },
            {
                'id': 3,
                'rental_agreement_id': 4,
                'charge_items': [
                    {'description': 'Base Rental (2 days)', 'amount': 150.00},
                    {'description': 'Child Seat', 'amount': 10.00}
                ],
                'total_amount': 160.00,
                'status': 'PAID',
                'created_at': '2025-12-12T09:00:00'
            },
            {
                'id': 4,
                'rental_agreement_id': 5,
                'charge_items': [
                    {'description': 'Base Rental (3 days)', 'amount': 270.00},
                    {'description': 'Extra Driver', 'amount': 45.00},
                    {'description': 'Fuel Charge', 'amount': 45.00},
                    {'description': 'Late Return', 'amount': 30.00}
                ],
                'total_amount': 390.00,
                'status': 'PAID',
                'created_at': '2025-12-11T21:00:00'
            },
            {
                'id': 5,
                'rental_agreement_id': 3,
                'charge_items': [
                    {'description': 'Base Rental (4 days)', 'amount': 600.00},
                    {'description': 'Premium Insurance', 'amount': 120.00}
                ],
                'total_amount': 720.00,
                'status': 'PENDING',
                'created_at': '2025-12-14T12:00:00'
            },
            {
                'id': 6,
                'rental_agreement_id': 6,
                'charge_items': [
                    {'description': 'Maybach S680 VIP Limousine Rental (4 days)', 'amount': 6000.00},
                    {'description': 'Premium Chauffeur Service', 'amount': 800.00},
                    {'description': 'Airport VIP Transfer', 'amount': 350.00},
                    {'description': 'Premium Insurance', 'amount': 400.00}
                ],
                'total_amount': 7550.00,
                'status': 'PENDING',
                'created_at': '2025-12-13T15:30:00'
            },
        ],
        'payments': [
            {
                'id': 1,
                'invoice_id': 1,
                'amount': 100.00,
                'status': 'COMPLETED',
                'timestamp': '2025-12-11T11:15:00'
            },
            {
                'id': 2,
                'invoice_id': 3,
                'amount': 160.00,
                'status': 'COMPLETED',
                'timestamp': '2025-12-12T09:30:00'
            },
            {
                'id': 3,
                'invoice_id': 4,
                'amount': 390.00,
                'status': 'COMPLETED',
                'timestamp': '2025-12-11T21:45:00'
            },
            {
                'id': 4,
                'invoice_id': 2,
                'amount': 100.00,
                'status': 'PENDING',
                'timestamp': '2025-12-12T10:00:00'
            },
        ],
        'notifications': [
            {
                'type': 'ReservationConfirmation',
                'recipient': 'irem.aslan@email.com',
                'message': 'Your Rolls Royce Ghost reservation has been confirmed!',
                'timestamp': now
            },
            {
                'type': 'PickupReminder',
                'recipient': 'can.somer@email.com',
                'message': 'Reminder: Your Maserati Ghibli pickup is tomorrow',
                'timestamp': '2025-12-11T18:00:00'
            },
            {
                'type': 'InvoiceSuccess',
                'recipient': 'beyza.aslan@email.com',
                'message': 'Payment received for invoice #1',
                'timestamp': '2025-12-11T11:16:00'
            },
            {
                'type': 'ReservationConfirmation',
                'recipient': 'guney.ulusoy@email.com',
                'message': 'Your Lamborghini Urus reservation has been confirmed!',
                'timestamp': '2025-12-13T10:00:00'
            },
            {
                'type': 'PickupReminder',
                'recipient': 'gaye.seker@email.com',
                'message': 'Reminder: Your van rental pickup is in 2 hours',
                'timestamp': '2025-12-15T06:00:00'
            },
            {
                'type': 'InvoiceSuccess',
                'recipient': 'berk.ozkoylu@email.com',
                'message': 'Payment received for Bentley rental',
                'timestamp': '2025-12-12T09:35:00'
            },
            {
                'type': 'ReturnReminder',
                'recipient': 'muhsin.yilmaz@email.com',
                'message': 'Reminder: Please return sedan by tomorrow',
                'timestamp': '2025-12-20T08:00:00'
            },
            {
                'type': 'MaintenanceAlert',
                'recipient': 'admin@crfms.com',
                'message': 'Ferrari 488 requires scheduled maintenance',
                'timestamp': '2025-12-11T07:00:00'
            },
            {
                'type': 'ReservationConfirmation',
                'recipient': 'ada.ergen@email.com',
                'message': 'Your Porsche 911 reservation has been confirmed!',
                'timestamp': '2025-12-15T14:00:00'
            },
            {
                'type': 'InvoiceSuccess',
                'recipient': 'ece.kaya@email.com',
                'message': 'Payment received for Ferrari rental',
                'timestamp': '2025-12-11T21:50:00'
            },
            {
                'type': 'ReservationConfirmation',
                'recipient': 'binnur.kurt@email.com',
                'message': 'Your VIP Maybach S680 limousine reservation has been confirmed! Premium chauffeur service included.',
                'timestamp': '2025-12-13T15:00:00'
            },
        ],
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
        print(f"   ✓ Loaded {len(loaded_data['reservations'])} reservations")
        print(f"   ✓ Loaded {len(loaded_data['rental_agreements'])} rental agreements")
        print(f"   ✓ Loaded {len(loaded_data['maintenance_records'])} maintenance records")
        print(f"   ✓ Loaded {len(loaded_data['invoices'])} invoices")
        print(f"   ✓ Loaded {len(loaded_data['payments'])} payments")
        print(f"   ✓ Loaded {len(loaded_data['notifications'])} notifications")
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
    
    # Add reservations
    for res in json_data.get('reservations', []):
        reservation = snapshot.reservations.add()
        reservation.id = res['id']
        reservation.customer_id = res['customer_id']
        reservation.vehicle_class_name = res['vehicle_class_name']
        reservation.location_id = res['location_id']
        reservation.pickup_time = res['pickup_time']
        reservation.return_time = res['return_time']
    
    # Add rental agreements
    for rental in json_data.get('rental_agreements', []):
        ra = snapshot.rental_agreements.add()
        ra.id = rental['id']
        ra.reservation_id = rental['reservation_id']
        ra.vehicle_id = rental['vehicle_id']
        ra.pickup_token = rental['pickup_token']
        ra.start_odometer.value = rental['start_odometer']
        if rental.get('end_odometer'):
            ra.end_odometer.value = rental['end_odometer']
        ra.start_fuel_level.level = rental['start_fuel_level']
        if rental.get('end_fuel_level'):
            ra.end_fuel_level.level = rental['end_fuel_level']
        ra.pickup_time = rental['pickup_time']
        ra.expected_return_time = rental['expected_return_time']
        if rental.get('actual_return_time'):
            ra.actual_return_time = rental['actual_return_time']
        for item in rental.get('charge_items', []):
            charge = ra.charge_items.add()
            charge.description = item['description']
            charge.amount.amount = item['amount']
            charge.amount.currency = "USD"
    
    # Add maintenance records
    for maint in json_data.get('maintenance_records', []):
        record = snapshot.maintenance_records.add()
        record.id = maint['id']
        record.vehicle_id = maint['vehicle_id']
        record.service_type = maint['service_type']
        record.odometer_threshold.value = maint['odometer_threshold']
        if maint.get('time_threshold'):
            record.time_threshold = maint['time_threshold']
        if maint.get('last_service_date'):
            record.last_service_date = maint['last_service_date']
        if maint.get('last_service_odometer'):
            record.last_service_odometer.value = maint['last_service_odometer']
    
    # Add invoices
    for inv in json_data.get('invoices', []):
        invoice = snapshot.invoices.add()
        invoice.id = inv['id']
        invoice.rental_agreement_id = inv['rental_agreement_id']
        for item in inv.get('charge_items', []):
            charge = invoice.charge_items.add()
            charge.description = item['description']
            charge.amount.amount = item['amount']
            charge.amount.currency = "USD"
        invoice.total_amount.amount = inv['total_amount']
        invoice.total_amount.currency = "USD"
        invoice.status = inv['status']
        invoice.created_at = inv['created_at']
    
    # Add payments
    for pay in json_data.get('payments', []):
        payment = snapshot.payments.add()
        payment.id = pay['id']
        payment.invoice_id = pay['invoice_id']
        payment.amount.amount = pay['amount']
        payment.amount.currency = "USD"
        payment.status = pay['status']
        payment.timestamp = pay['timestamp']
    
    # Add notifications
    for notif in json_data.get('notifications', []):
        notification = snapshot.notifications.add()
        notification.type = notif['type']
        notification.recipient = notif['recipient']
        notification.message = notif['message']
        notification.timestamp = notif['timestamp']
    
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
        print(f"   ✓ Loaded {len(loaded_snapshot.reservations)} reservations")
        print(f"   ✓ Loaded {len(loaded_snapshot.rental_agreements)} rental agreements")
        print(f"   ✓ Loaded {len(loaded_snapshot.maintenance_records)} maintenance records")
        print(f"   ✓ Loaded {len(loaded_snapshot.invoices)} invoices")
        print(f"   ✓ Loaded {len(loaded_snapshot.payments)} payments")
        print(f"   ✓ Loaded {len(loaded_snapshot.notifications)} notifications")
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
