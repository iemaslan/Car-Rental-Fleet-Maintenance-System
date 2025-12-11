"""
Protocol Buffers Persistence for CRFMS.
Handles saving and loading system snapshots to/from binary Protobuf files.
"""
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path

from domain.models import (
    Customer, Vehicle, VehicleClass, Location, Reservation,
    RentalAgreement, MaintenanceRecord, Invoice, Payment, Notification
)
from domain.value_objects import Money, FuelLevel, Kilometers
from domain.audit_log import AuditEntry, AuditEventType

# Import generated protobuf classes
from persistence import crfms_pb2


class ProtobufPersistence:
    """Handles Protocol Buffers serialization and deserialization of CRFMS state."""
    
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
        Save complete system state to binary Protobuf file.
        
        Args:
            filename: Path to output protobuf file
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
        snapshot = crfms_pb2.CrfmsSnapshot()
        
        # Set metadata
        snapshot.metadata.version = "1.0"
        snapshot.metadata.timestamp = datetime.now().isoformat()
        snapshot.metadata.description = "CRFMS System Snapshot"
        
        # Serialize all entities
        for customer in customers:
            snapshot.customers.append(ProtobufPersistence._to_proto_customer(customer))
        
        for vehicle in vehicles:
            snapshot.vehicles.append(ProtobufPersistence._to_proto_vehicle(vehicle))
        
        for reservation in reservations:
            snapshot.reservations.append(ProtobufPersistence._to_proto_reservation(reservation))
        
        for rental in rental_agreements:
            snapshot.rental_agreements.append(ProtobufPersistence._to_proto_rental_agreement(rental))
        
        for record in maintenance_records:
            snapshot.maintenance_records.append(ProtobufPersistence._to_proto_maintenance_record(record))
        
        for invoice in invoices:
            snapshot.invoices.append(ProtobufPersistence._to_proto_invoice(invoice))
        
        for payment in payments:
            snapshot.payments.append(ProtobufPersistence._to_proto_payment(payment))
        
        for notification in notifications:
            snapshot.notifications.append(ProtobufPersistence._to_proto_notification(notification))
        
        if audit_entries:
            for entry in audit_entries:
                snapshot.audit_entries.append(ProtobufPersistence._to_proto_audit_entry(entry))
        
        # Write to binary file
        with open(filename, mode='wb') as f:
            f.write(snapshot.SerializeToString())
    
    @staticmethod
    def load_snapshot(filename: str) -> Dict[str, List[Any]]:
        """
        Load complete system state from binary Protobuf file.
        
        Args:
            filename: Path to input protobuf file
            
        Returns:
            Dictionary containing protobuf message objects
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not Path(filename).exists():
            raise FileNotFoundError(f"Snapshot file not found: {filename}")
        
        snapshot = crfms_pb2.CrfmsSnapshot()
        
        with open(filename, mode='rb') as f:
            snapshot.ParseFromString(f.read())
        
        # Return protobuf messages (deserialization to domain objects handled by conversion utility)
        return {
            'metadata': {
                'version': snapshot.metadata.version,
                'timestamp': snapshot.metadata.timestamp,
                'description': snapshot.metadata.description
            },
            'customers': list(snapshot.customers),
            'vehicles': list(snapshot.vehicles),
            'reservations': list(snapshot.reservations),
            'rental_agreements': list(snapshot.rental_agreements),
            'maintenance_records': list(snapshot.maintenance_records),
            'invoices': list(snapshot.invoices),
            'payments': list(snapshot.payments),
            'notifications': list(snapshot.notifications),
            'audit_entries': list(snapshot.audit_entries)
        }
    
    # Conversion to Protobuf messages
    
    @staticmethod
    def _to_proto_money(money: Money) -> crfms_pb2.Money:
        proto = crfms_pb2.Money()
        proto.amount = float(money.amount)
        proto.currency = "USD"
        return proto
    
    @staticmethod
    def _to_proto_kilometers(km: Kilometers) -> crfms_pb2.Kilometers:
        proto = crfms_pb2.Kilometers()
        proto.value = km.value
        return proto
    
    @staticmethod
    def _to_proto_fuel_level(fuel: FuelLevel) -> crfms_pb2.FuelLevel:
        proto = crfms_pb2.FuelLevel()
        proto.level = fuel.level
        return proto
    
    @staticmethod
    def _to_proto_customer(customer: Customer) -> crfms_pb2.Customer:
        proto = crfms_pb2.Customer()
        proto.id = customer.id
        proto.name = customer.name
        proto.email = customer.email
        proto.phone = customer.phone
        proto.drivers_license = customer.drivers_license
        return proto
    
    @staticmethod
    def _to_proto_vehicle_class(vc: VehicleClass) -> crfms_pb2.VehicleClass:
        proto = crfms_pb2.VehicleClass()
        proto.name = vc.name
        proto.base_rate.CopyFrom(ProtobufPersistence._to_proto_money(vc.base_rate))
        proto.daily_mileage_allowance = vc.daily_mileage_allowance
        return proto
    
    @staticmethod
    def _to_proto_location(loc: Location) -> crfms_pb2.Location:
        proto = crfms_pb2.Location()
        proto.id = loc.id
        proto.name = loc.name
        proto.address = loc.address
        return proto
    
    @staticmethod
    def _to_proto_vehicle(vehicle: Vehicle) -> crfms_pb2.Vehicle:
        proto = crfms_pb2.Vehicle()
        proto.id = vehicle.id
        proto.vehicle_class.CopyFrom(ProtobufPersistence._to_proto_vehicle_class(vehicle.vehicle_class))
        proto.location.CopyFrom(ProtobufPersistence._to_proto_location(vehicle.location))
        proto.status = vehicle.status.value
        proto.odometer.CopyFrom(ProtobufPersistence._to_proto_kilometers(vehicle.odometer))
        proto.fuel_level.CopyFrom(ProtobufPersistence._to_proto_fuel_level(vehicle.fuel_level))
        return proto
    
    @staticmethod
    def _to_proto_reservation(reservation: Reservation) -> crfms_pb2.Reservation:
        proto = crfms_pb2.Reservation()
        proto.id = reservation.id
        proto.customer_id = reservation.customer.id
        proto.vehicle_class_name = reservation.vehicle_class.name
        proto.location_id = reservation.location.id
        proto.pickup_time = reservation.pickup_time.isoformat()
        proto.return_time = reservation.return_time.isoformat()
        proto.addons.extend(reservation.addons)
        proto.insurance_tier = reservation.insurance_tier
        return proto
    
    @staticmethod
    def _to_proto_charge_item(description: str, amount: Money) -> crfms_pb2.ChargeItem:
        proto = crfms_pb2.ChargeItem()
        proto.description = description
        proto.amount.CopyFrom(ProtobufPersistence._to_proto_money(amount))
        return proto
    
    @staticmethod
    def _to_proto_rental_agreement(rental: RentalAgreement) -> crfms_pb2.RentalAgreement:
        proto = crfms_pb2.RentalAgreement()
        proto.id = rental.id
        proto.reservation_id = rental.reservation.id
        proto.vehicle_id = rental.vehicle.id
        proto.pickup_token = rental.pickup_token
        proto.start_odometer.CopyFrom(ProtobufPersistence._to_proto_kilometers(rental.start_odometer))
        if rental.end_odometer:
            proto.end_odometer.CopyFrom(ProtobufPersistence._to_proto_kilometers(rental.end_odometer))
        proto.start_fuel_level.CopyFrom(ProtobufPersistence._to_proto_fuel_level(rental.start_fuel_level))
        if rental.end_fuel_level:
            proto.end_fuel_level.CopyFrom(ProtobufPersistence._to_proto_fuel_level(rental.end_fuel_level))
        proto.pickup_time = rental.pickup_time.isoformat()
        proto.expected_return_time = rental.expected_return_time.isoformat()
        if rental.actual_return_time:
            proto.actual_return_time = rental.actual_return_time.isoformat()
        for item in rental.charge_items:
            proto.charge_items.append(ProtobufPersistence._to_proto_charge_item(item.description, item.amount))
        return proto
    
    @staticmethod
    def _to_proto_maintenance_record(record: MaintenanceRecord) -> crfms_pb2.MaintenanceRecord:
        proto = crfms_pb2.MaintenanceRecord()
        proto.id = record.id
        proto.vehicle_id = record.vehicle.id
        proto.service_type = record.service_type
        proto.odometer_threshold.CopyFrom(ProtobufPersistence._to_proto_kilometers(record.odometer_threshold))
        if record.time_threshold:
            proto.time_threshold = record.time_threshold.isoformat()
        if record.last_service_date:
            proto.last_service_date = record.last_service_date.isoformat()
        if record.last_service_odometer:
            proto.last_service_odometer.CopyFrom(ProtobufPersistence._to_proto_kilometers(record.last_service_odometer))
        return proto
    
    @staticmethod
    def _to_proto_invoice(invoice: Invoice) -> crfms_pb2.Invoice:
        proto = crfms_pb2.Invoice()
        proto.id = invoice.id
        proto.rental_agreement_id = invoice.rental_agreement.id
        for item in invoice.charge_items:
            proto.charge_items.append(ProtobufPersistence._to_proto_charge_item(item.description, item.amount))
        proto.total_amount.CopyFrom(ProtobufPersistence._to_proto_money(invoice.total_amount))
        proto.status = invoice.status
        proto.created_at = invoice.created_at.isoformat()
        return proto
    
    @staticmethod
    def _to_proto_payment(payment: Payment) -> crfms_pb2.Payment:
        proto = crfms_pb2.Payment()
        proto.id = payment.id
        proto.invoice_id = payment.invoice.id
        proto.amount.CopyFrom(ProtobufPersistence._to_proto_money(payment.amount))
        proto.payment_method = payment.payment_method
        proto.transaction_id = payment.transaction_id
        proto.status = payment.status
        proto.timestamp = payment.timestamp.isoformat()
        return proto
    
    @staticmethod
    def _to_proto_notification(notification: Notification) -> crfms_pb2.Notification:
        proto = crfms_pb2.Notification()
        proto.id = notification.id
        proto.recipient = notification.recipient
        proto.type = notification.type
        proto.message = notification.message
        proto.timestamp = notification.timestamp.isoformat()
        proto.sent = notification.sent
        return proto
    
    @staticmethod
    def _to_proto_audit_entry(entry: AuditEntry) -> crfms_pb2.AuditEntry:
        proto = crfms_pb2.AuditEntry()
        proto.id = entry.id
        proto.timestamp = entry.timestamp.isoformat()
        proto.event_type = entry.event_type.value
        proto.actor_type = entry.actor_type
        proto.actor_id = entry.actor_id
        proto.actor_name = entry.actor_name
        proto.entity_type = entry.entity_type
        proto.entity_id = entry.entity_id
        proto.description = entry.description
        if entry.metadata:
            for key, value in entry.metadata.items():
                proto.metadata[key] = str(value)
        return proto
