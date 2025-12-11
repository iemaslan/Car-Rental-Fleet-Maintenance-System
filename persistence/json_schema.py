"""
JSON Schema validation for CRFMS snapshots.
Validates snapshot structure and data integrity.
"""

from typing import Dict, Any, List
from datetime import datetime


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class JSONSchemaValidator:
    """Validator for CRFMS JSON snapshots."""
    
    @staticmethod
    def validate_customer(customer: Dict[str, Any], index: int) -> List[str]:
        """Validate customer object."""
        errors = []
        
        if 'id' not in customer:
            errors.append(f"Customer #{index}: Missing 'id' field")
        elif not isinstance(customer['id'], int):
            errors.append(f"Customer #{index}: 'id' must be an integer")
        
        if 'name' not in customer:
            errors.append(f"Customer #{index}: Missing 'name' field")
        elif not isinstance(customer['name'], str) or not customer['name'].strip():
            errors.append(f"Customer #{index}: 'name' must be a non-empty string")
        
        if 'email' not in customer:
            errors.append(f"Customer #{index}: Missing 'email' field")
        elif not isinstance(customer['email'], str) or '@' not in customer['email']:
            errors.append(f"Customer #{index}: Invalid email format")
        
        if 'phone' in customer and not isinstance(customer['phone'], str):
            errors.append(f"Customer #{index}: 'phone' must be a string")
        
        return errors
    
    @staticmethod
    def validate_vehicle(vehicle: Dict[str, Any], index: int) -> List[str]:
        """Validate vehicle object."""
        errors = []
        
        if 'id' not in vehicle:
            errors.append(f"Vehicle #{index}: Missing 'id' field")
        elif not isinstance(vehicle['id'], int):
            errors.append(f"Vehicle #{index}: 'id' must be an integer")
        
        if 'vehicle_class' not in vehicle:
            errors.append(f"Vehicle #{index}: Missing 'vehicle_class' field")
        elif not isinstance(vehicle['vehicle_class'], dict):
            errors.append(f"Vehicle #{index}: 'vehicle_class' must be an object")
        else:
            vc = vehicle['vehicle_class']
            if 'name' not in vc:
                errors.append(f"Vehicle #{index}: vehicle_class missing 'name'")
            if 'base_rate' not in vc:
                errors.append(f"Vehicle #{index}: vehicle_class missing 'base_rate'")
            elif not isinstance(vc['base_rate'], (int, float)) or vc['base_rate'] < 0:
                errors.append(f"Vehicle #{index}: base_rate must be a non-negative number")
        
        valid_statuses = ['AVAILABLE', 'RENTED', 'MAINTENANCE', 'OUT_OF_SERVICE']
        if 'status' in vehicle and vehicle['status'] not in valid_statuses:
            errors.append(f"Vehicle #{index}: Invalid status '{vehicle['status']}'")
        
        if 'odometer' in vehicle:
            if not isinstance(vehicle['odometer'], (int, float)) or vehicle['odometer'] < 0:
                errors.append(f"Vehicle #{index}: odometer must be a non-negative number")
        
        return errors
    
    @staticmethod
    def validate_reservation(reservation: Dict[str, Any], index: int) -> List[str]:
        """Validate reservation object."""
        errors = []
        
        required_fields = ['id', 'customer_id', 'vehicle_class_name', 'pickup_time', 'return_time']
        for field in required_fields:
            if field not in reservation:
                errors.append(f"Reservation #{index}: Missing '{field}' field")
        
        if 'id' in reservation and not isinstance(reservation['id'], int):
            errors.append(f"Reservation #{index}: 'id' must be an integer")
        
        if 'customer_id' in reservation and not isinstance(reservation['customer_id'], int):
            errors.append(f"Reservation #{index}: 'customer_id' must be an integer")
        
        # Validate datetime strings
        for time_field in ['pickup_time', 'return_time']:
            if time_field in reservation:
                try:
                    datetime.fromisoformat(reservation[time_field].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    errors.append(f"Reservation #{index}: '{time_field}' must be valid ISO datetime")
        
        return errors
    
    @staticmethod
    def validate_rental_agreement(rental: Dict[str, Any], index: int) -> List[str]:
        """Validate rental agreement object."""
        errors = []
        
        required_fields = ['id', 'reservation_id', 'vehicle_id']
        for field in required_fields:
            if field not in rental:
                errors.append(f"Rental #{index}: Missing '{field}' field")
        
        if 'charge_items' in rental:
            if not isinstance(rental['charge_items'], list):
                errors.append(f"Rental #{index}: 'charge_items' must be an array")
            else:
                for i, item in enumerate(rental['charge_items']):
                    if 'amount' not in item:
                        errors.append(f"Rental #{index}, charge_item #{i}: Missing 'amount'")
                    elif not isinstance(item['amount'], (int, float)) or item['amount'] < 0:
                        errors.append(f"Rental #{index}, charge_item #{i}: 'amount' must be non-negative")
        
        return errors
    
    @staticmethod
    def validate_invoice(invoice: Dict[str, Any], index: int) -> List[str]:
        """Validate invoice object."""
        errors = []
        
        if 'id' not in invoice:
            errors.append(f"Invoice #{index}: Missing 'id' field")
        
        if 'total_amount' in invoice:
            if not isinstance(invoice['total_amount'], (int, float)) or invoice['total_amount'] < 0:
                errors.append(f"Invoice #{index}: 'total_amount' must be non-negative")
        
        valid_statuses = ['PENDING', 'PAID', 'OVERDUE', 'CANCELLED']
        if 'status' in invoice and invoice['status'] not in valid_statuses:
            errors.append(f"Invoice #{index}: Invalid status '{invoice['status']}'")
        
        return errors
    
    @staticmethod
    def validate_snapshot(snapshot: Dict[str, Any]) -> List[str]:
        """
        Validate entire snapshot structure.
        
        Returns:
            List of validation error messages. Empty list if valid.
        """
        errors = []
        
        # Validate metadata
        if 'metadata' in snapshot:
            metadata = snapshot['metadata']
            if not isinstance(metadata, dict):
                errors.append("'metadata' must be an object")
            else:
                if 'version' in metadata and not isinstance(metadata['version'], str):
                    errors.append("metadata.version must be a string")
                if 'timestamp' in metadata:
                    try:
                        datetime.fromisoformat(metadata['timestamp'].replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        errors.append("metadata.timestamp must be valid ISO datetime")
        
        # Validate customers
        if 'customers' in snapshot:
            if not isinstance(snapshot['customers'], list):
                errors.append("'customers' must be an array")
            else:
                for i, customer in enumerate(snapshot['customers'], 1):
                    errors.extend(JSONSchemaValidator.validate_customer(customer, i))
        
        # Validate vehicles
        if 'vehicles' in snapshot:
            if not isinstance(snapshot['vehicles'], list):
                errors.append("'vehicles' must be an array")
            else:
                for i, vehicle in enumerate(snapshot['vehicles'], 1):
                    errors.extend(JSONSchemaValidator.validate_vehicle(vehicle, i))
        
        # Validate reservations
        if 'reservations' in snapshot:
            if not isinstance(snapshot['reservations'], list):
                errors.append("'reservations' must be an array")
            else:
                for i, reservation in enumerate(snapshot['reservations'], 1):
                    errors.extend(JSONSchemaValidator.validate_reservation(reservation, i))
        
        # Validate rental agreements
        if 'rental_agreements' in snapshot:
            if not isinstance(snapshot['rental_agreements'], list):
                errors.append("'rental_agreements' must be an array")
            else:
                for i, rental in enumerate(snapshot['rental_agreements'], 1):
                    errors.extend(JSONSchemaValidator.validate_rental_agreement(rental, i))
        
        # Validate invoices
        if 'invoices' in snapshot:
            if not isinstance(snapshot['invoices'], list):
                errors.append("'invoices' must be an array")
            else:
                for i, invoice in enumerate(snapshot['invoices'], 1):
                    errors.extend(JSONSchemaValidator.validate_invoice(invoice, i))
        
        return errors
    
    @staticmethod
    def validate_or_raise(snapshot: Dict[str, Any]) -> None:
        """
        Validate snapshot and raise ValidationError if invalid.
        
        Args:
            snapshot: The snapshot dictionary to validate
            
        Raises:
            ValidationError: If validation fails
        """
        errors = JSONSchemaValidator.validate_snapshot(snapshot)
        if errors:
            error_msg = "Snapshot validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValidationError(error_msg)
