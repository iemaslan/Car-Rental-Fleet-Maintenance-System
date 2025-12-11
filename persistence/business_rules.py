"""
Business rule validation for CRFMS domain objects.
Validates business logic constraints and relationships.
"""

from typing import Dict, Any, List
from datetime import datetime


class BusinessRuleViolation(Exception):
    """Raised when a business rule is violated."""
    pass


class BusinessRuleValidator:
    """Validator for CRFMS business rules."""
    
    @staticmethod
    def validate_reservation_dates(reservation: Dict[str, Any]) -> List[str]:
        """Validate that reservation dates are logical."""
        errors = []
        
        try:
            pickup = datetime.fromisoformat(reservation['pickup_time'].replace('Z', '+00:00'))
            return_time = datetime.fromisoformat(reservation['return_time'].replace('Z', '+00:00'))
            
            if return_time <= pickup:
                errors.append(f"Reservation {reservation.get('id')}: Return time must be after pickup time")
            
            # Check if reservation is too far in the future (e.g., more than 1 year)
            now = datetime.now(pickup.tzinfo) if pickup.tzinfo else datetime.now()
            if (pickup - now).days > 365:
                errors.append(f"Reservation {reservation.get('id')}: Pickup date is more than 1 year in future")
            
        except (KeyError, ValueError, AttributeError):
            pass  # Skip if dates are missing or invalid (caught by schema validation)
        
        return errors
    
    @staticmethod
    def validate_rental_odometer(rental: Dict[str, Any]) -> List[str]:
        """Validate that rental odometer readings are consistent."""
        errors = []
        
        start_odo = rental.get('start_odometer')
        end_odo = rental.get('end_odometer')
        
        if start_odo is not None and end_odo is not None:
            if end_odo < start_odo:
                errors.append(
                    f"Rental {rental.get('id')}: End odometer ({end_odo}) "
                    f"cannot be less than start odometer ({start_odo})"
                )
            
            # Check for unrealistic mileage (e.g., more than 5000 km in one rental)
            if end_odo - start_odo > 5000:
                errors.append(
                    f"Rental {rental.get('id')}: Mileage exceeds 5000 km "
                    f"({end_odo - start_odo} km), please verify"
                )
        
        return errors
    
    @staticmethod
    def validate_vehicle_availability(snapshot: Dict[str, Any]) -> List[str]:
        """Validate that vehicles are not double-booked."""
        errors = []
        
        vehicles = {v['id']: v for v in snapshot.get('vehicles', [])}
        rentals = snapshot.get('rental_agreements', [])
        
        # Get active rentals (no return time)
        active_rentals = [r for r in rentals if not r.get('actual_return_time')]
        
        # Check each vehicle
        for vehicle_id, vehicle in vehicles.items():
            status = vehicle.get('status')
            active_rental_count = sum(1 for r in active_rentals if r.get('vehicle_id') == vehicle_id)
            
            if status == 'RENTED' and active_rental_count == 0:
                errors.append(
                    f"Vehicle {vehicle_id}: Status is RENTED but no active rental agreement found"
                )
            elif status == 'AVAILABLE' and active_rental_count > 0:
                errors.append(
                    f"Vehicle {vehicle_id}: Status is AVAILABLE but has {active_rental_count} active rental(s)"
                )
            elif active_rental_count > 1:
                errors.append(
                    f"Vehicle {vehicle_id}: Multiple active rentals ({active_rental_count}) - possible double booking"
                )
        
        return errors
    
    @staticmethod
    def validate_customer_reservations(snapshot: Dict[str, Any]) -> List[str]:
        """Validate customer-reservation relationships."""
        errors = []
        
        customer_ids = {c['id'] for c in snapshot.get('customers', []) if 'id' in c}
        reservations = snapshot.get('reservations', [])
        
        for reservation in reservations:
            customer_id = reservation.get('customer_id')
            if customer_id and customer_id not in customer_ids:
                errors.append(
                    f"Reservation {reservation.get('id')}: References non-existent customer {customer_id}"
                )
        
        return errors
    
    @staticmethod
    def validate_invoice_amounts(invoice: Dict[str, Any]) -> List[str]:
        """Validate that invoice total matches charge items."""
        errors = []
        
        charge_items = invoice.get('charge_items', [])
        total_amount = invoice.get('total_amount', 0)
        
        if charge_items:
            calculated_total = sum(item.get('amount', 0) for item in charge_items)
            # Allow small floating point differences
            if abs(calculated_total - total_amount) > 0.01:
                errors.append(
                    f"Invoice {invoice.get('id')}: Total amount (${total_amount:.2f}) "
                    f"doesn't match sum of charge items (${calculated_total:.2f})"
                )
        
        return errors
    
    @staticmethod
    def validate_payment_amounts(snapshot: Dict[str, Any]) -> List[str]:
        """Validate payment amounts against invoices."""
        errors = []
        
        invoices = {inv['id']: inv for inv in snapshot.get('invoices', []) if 'id' in inv}
        payments = snapshot.get('payments', [])
        
        for payment in payments:
            invoice_id = payment.get('invoice_id')
            payment_amount = payment.get('amount', 0)
            
            if invoice_id and invoice_id in invoices:
                invoice_total = invoices[invoice_id].get('total_amount', 0)
                
                if payment_amount > invoice_total:
                    errors.append(
                        f"Payment {payment.get('id')}: Amount (${payment_amount:.2f}) "
                        f"exceeds invoice total (${invoice_total:.2f})"
                    )
        
        return errors
    
    @staticmethod
    def validate_maintenance_schedule(maintenance: Dict[str, Any]) -> List[str]:
        """Validate maintenance scheduling logic."""
        errors = []
        
        last_service_odo = maintenance.get('last_service_odometer')
        odo_threshold = maintenance.get('odometer_threshold')
        
        if last_service_odo is not None and odo_threshold is not None:
            if odo_threshold <= last_service_odo:
                errors.append(
                    f"Maintenance {maintenance.get('id')}: Odometer threshold ({odo_threshold}) "
                    f"should be greater than last service odometer ({last_service_odo})"
                )
        
        return errors
    
    @staticmethod
    def validate_snapshot(snapshot: Dict[str, Any]) -> List[str]:
        """
        Validate all business rules for a snapshot.
        
        Returns:
            List of business rule violation messages. Empty list if all rules pass.
        """
        errors = []
        
        # Validate reservation dates
        for reservation in snapshot.get('reservations', []):
            errors.extend(BusinessRuleValidator.validate_reservation_dates(reservation))
        
        # Validate rental odometer readings
        for rental in snapshot.get('rental_agreements', []):
            errors.extend(BusinessRuleValidator.validate_rental_odometer(rental))
        
        # Validate vehicle availability
        errors.extend(BusinessRuleValidator.validate_vehicle_availability(snapshot))
        
        # Validate customer references
        errors.extend(BusinessRuleValidator.validate_customer_reservations(snapshot))
        
        # Validate invoice amounts
        for invoice in snapshot.get('invoices', []):
            errors.extend(BusinessRuleValidator.validate_invoice_amounts(invoice))
        
        # Validate payment amounts
        errors.extend(BusinessRuleValidator.validate_payment_amounts(snapshot))
        
        # Validate maintenance schedules
        for maintenance in snapshot.get('maintenance_records', []):
            errors.extend(BusinessRuleValidator.validate_maintenance_schedule(maintenance))
        
        return errors
    
    @staticmethod
    def validate_or_raise(snapshot: Dict[str, Any]) -> None:
        """
        Validate snapshot and raise BusinessRuleViolation if any rule is violated.
        
        Args:
            snapshot: The snapshot dictionary to validate
            
        Raises:
            BusinessRuleViolation: If any business rule is violated
        """
        errors = BusinessRuleValidator.validate_snapshot(snapshot)
        if errors:
            error_msg = "Business rule validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise BusinessRuleViolation(error_msg)
