"""
JSON Persistence for CRFMS.
Handles saving and loading system snapshots to/from JSON files.
"""
import json
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from domain.models import (
    Customer, Vehicle, VehicleClass, Location, Reservation, 
    RentalAgreement, MaintenanceRecord, Invoice, Payment, Notification
)
from domain.value_objects import Money, FuelLevel, Kilometers
from domain.audit_log import AuditLogger, AuditEntry, AuditEventType


class JSONPersistence:
    """Handles JSON serialization and deserialization of CRFMS state."""
    
    @staticmethod
    def save_snapshot(
        filename: str,
        customers: List[Customer],
        vehicles: List[Vehicle],
        reservations: List[Reservation],
        rental_agreements: List[RentalAgreement],
        maintenance_records: List[MaintenanceRecord],
        invoices: List[Invoice],
        payments: List[Payment],
        notifications: List[Notification],
        audit_entries: List[AuditEntry] = None
    ) -> None:
        """
        Save complete system state to JSON file.
        
        Args:
            filename: Path to output JSON file
            customers: List of all customers
            vehicles: List of all vehicles
            reservations: List of all reservations
            rental_agreements: List of all rental agreements
            maintenance_records: List of all maintenance records
            invoices: List of all invoices
            payments: List of all payments
            notifications: List of all notifications
            audit_entries: Optional list of audit log entries
        """
        snapshot = {
            'metadata': {
                'version': '1.0',
                'timestamp': datetime.now().isoformat(),
                'description': 'CRFMS System Snapshot'
            },
            'customers': [JSONPersistence._serialize_customer(c) for c in customers],
            'vehicles': [JSONPersistence._serialize_vehicle(v) for v in vehicles],
            'reservations': [JSONPersistence._serialize_reservation(r) for r in reservations],
            'rental_agreements': [JSONPersistence._serialize_rental_agreement(r) for r in rental_agreements],
            'maintenance_records': [JSONPersistence._serialize_maintenance_record(m) for m in maintenance_records],
            'invoices': [JSONPersistence._serialize_invoice(i) for i in invoices],
            'payments': [JSONPersistence._serialize_payment(p) for p in payments],
            'notifications': [JSONPersistence._serialize_notification(n) for n in notifications],
        }
        
        if audit_entries:
            snapshot['audit_entries'] = [JSONPersistence._serialize_audit_entry(e) for e in audit_entries]
        
        # Write to file with proper context manager
        with open(filename, mode='wt', encoding='utf-8') as f:
            json.dump(snapshot, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def load_snapshot(filename: str) -> Dict[str, List[Any]]:
        """
        Load complete system state from JSON file.
        
        Args:
            filename: Path to input JSON file
            
        Returns:
            Dictionary containing lists of domain objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON
        """
        if not Path(filename).exists():
            raise FileNotFoundError(f"Snapshot file not found: {filename}")
        
        with open(filename, mode='rt', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        # Deserialize all entities
        result = {
            'customers': [JSONPersistence._deserialize_customer(c) for c in snapshot.get('customers', [])],
            'vehicles': [JSONPersistence._deserialize_vehicle(v) for v in snapshot.get('vehicles', [])],
            'reservations': [JSONPersistence._deserialize_reservation(r) for r in snapshot.get('reservations', [])],
            'rental_agreements': [JSONPersistence._deserialize_rental_agreement(r) for r in snapshot.get('rental_agreements', [])],
            'maintenance_records': [JSONPersistence._deserialize_maintenance_record(m) for m in snapshot.get('maintenance_records', [])],
            'invoices': [JSONPersistence._deserialize_invoice(i) for i in snapshot.get('invoices', [])],
            'payments': [JSONPersistence._deserialize_payment(p) for p in snapshot.get('payments', [])],
            'notifications': [JSONPersistence._deserialize_notification(n) for n in snapshot.get('notifications', [])],
        }
        
        if 'audit_entries' in snapshot:
            result['audit_entries'] = [JSONPersistence._deserialize_audit_entry(e) for e in snapshot['audit_entries']]
        
        return result
    
    # Serialization methods
    
    @staticmethod
    def _serialize_customer(customer: Customer) -> Dict:
        return {
            'id': customer.id,
            'name': customer.name,
            'email': customer.email,
            'phone': customer.phone
        }
    
    @staticmethod
    def _serialize_vehicle(vehicle: Vehicle) -> Dict:
        return {
            'id': vehicle.id,
            'vehicle_class': {
                'name': vehicle.vehicle_class.name,
                'base_rate': float(vehicle.vehicle_class.base_rate.amount),
                'daily_mileage_allowance': vehicle.vehicle_class.daily_mileage_allowance
            },
            'location': {
                'id': vehicle.location.id,
                'name': vehicle.location.name,
                'address': vehicle.location.address
            },
            'status': vehicle.status.value,
            'odometer': vehicle.odometer.value,
            'fuel_level': vehicle.fuel_level.level
        }
    
    @staticmethod
    def _serialize_reservation(reservation: Reservation) -> Dict:
        return {
            'id': reservation.id,
            'customer_id': reservation.customer.id,
            'vehicle_class_name': reservation.vehicle_class.name,
            'location_id': reservation.location.id,
            'pickup_time': reservation.pickup_time.isoformat(),
            'return_time': reservation.return_time.isoformat(),
            'addons': reservation.addons,
            'insurance_tier': reservation.insurance_tier
        }
    
    @staticmethod
    def _serialize_rental_agreement(rental: RentalAgreement) -> Dict:
        return {
            'id': rental.id,
            'reservation_id': rental.reservation.id,
            'vehicle_id': rental.vehicle.id,
            'pickup_token': rental.pickup_token,
            'start_odometer': rental.start_odometer.value,
            'end_odometer': rental.end_odometer.value if rental.end_odometer else None,
            'start_fuel_level': rental.start_fuel_level.level,
            'end_fuel_level': rental.end_fuel_level.level if rental.end_fuel_level else None,
            'pickup_time': rental.pickup_time.isoformat(),
            'expected_return_time': rental.expected_return_time.isoformat(),
            'actual_return_time': rental.actual_return_time.isoformat() if rental.actual_return_time else None,
            'charge_items': [
                {'description': item.description, 'amount': float(item.amount.amount)}
                for item in rental.charge_items
            ]
        }
    
    @staticmethod
    def _serialize_maintenance_record(record: MaintenanceRecord) -> Dict:
        return {
            'id': record.id,
            'vehicle_id': record.vehicle.id,
            'service_type': record.service_type,
            'odometer_threshold': record.odometer_threshold.value,
            'time_threshold': record.time_threshold.isoformat() if record.time_threshold else None,
            'last_service_date': record.last_service_date.isoformat() if record.last_service_date else None,
            'last_service_odometer': record.last_service_odometer.value if record.last_service_odometer else None
        }
    
    @staticmethod
    def _serialize_invoice(invoice: Invoice) -> Dict:
        return {
            'id': invoice.id,
            'rental_agreement_id': invoice.rental_agreement.id,
            'charge_items': [
                {'description': item.description, 'amount': float(item.amount.amount)}
                for item in invoice.charge_items
            ],
            'total_amount': float(invoice.total_amount.amount),
            'status': invoice.status,
            'created_at': invoice.created_at.isoformat()
        }
    
    @staticmethod
    def _serialize_payment(payment: Payment) -> Dict:
        return {
            'id': payment.id,
            'invoice_id': payment.invoice.id,
            'amount': float(payment.amount.amount),
            'payment_method': payment.payment_method,
            'transaction_id': payment.transaction_id,
            'status': payment.status,
            'timestamp': payment.timestamp.isoformat()
        }
    
    @staticmethod
    def _serialize_notification(notification: Notification) -> Dict:
        return {
            'id': notification.id,
            'recipient': notification.recipient,
            'type': notification.type,
            'message': notification.message,
            'timestamp': notification.timestamp.isoformat(),
            'sent': notification.sent
        }
    
    @staticmethod
    def _serialize_audit_entry(entry: AuditEntry) -> Dict:
        return {
            'id': entry.id,
            'timestamp': entry.timestamp.isoformat(),
            'event_type': entry.event_type.value,
            'actor_type': entry.actor_type,
            'actor_id': entry.actor_id,
            'actor_name': entry.actor_name,
            'entity_type': entry.entity_type,
            'entity_id': entry.entity_id,
            'description': entry.description,
            'metadata': entry.metadata
        }
    
    # Deserialization methods (simplified - assumes objects exist or creates stubs)
    
    @staticmethod
    def _deserialize_customer(data: Dict) -> Customer:
        return Customer(
            id=data['id'],
            name=data['name'],
            email=data['email'],
            phone=data['phone']
        )
    
    @staticmethod
    def _deserialize_vehicle(data: Dict) -> Dict:
        """Returns dict since we need to reconstruct relationships."""
        return data
    
    @staticmethod
    def _deserialize_reservation(data: Dict) -> Dict:
        """Returns dict since we need to reconstruct relationships."""
        return data
    
    @staticmethod
    def _deserialize_rental_agreement(data: Dict) -> Dict:
        """Returns dict since we need to reconstruct relationships."""
        return data
    
    @staticmethod
    def _deserialize_maintenance_record(data: Dict) -> Dict:
        """Returns dict since we need to reconstruct relationships."""
        return data
    
    @staticmethod
    def _deserialize_invoice(data: Dict) -> Dict:
        """Returns dict since we need to reconstruct relationships."""
        return data
    
    @staticmethod
    def _deserialize_payment(data: Dict) -> Dict:
        """Returns dict since we need to reconstruct relationships."""
        return data
    
    @staticmethod
    def _deserialize_notification(data: Dict) -> Notification:
        return Notification(
            id=data['id'],
            recipient=data['recipient'],
            type=data['type'],
            message=data['message'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            sent=data['sent']
        )
    
    @staticmethod
    def _deserialize_audit_entry(data: Dict) -> Dict:
        """Returns dict representation."""
        return data
