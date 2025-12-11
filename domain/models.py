"""
Domain models for the Car Rental & Fleet Maintenance System.
These represent the core entities and their relationships.
"""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum
from datetime import datetime
from .value_objects import Money, FuelLevel, Kilometers


class VehicleStatus(Enum):
    """Enumeration of possible vehicle states."""
    AVAILABLE = "Available"
    RESERVED = "Reserved"
    RENTED = "Rented"
    OUT_OF_SERVICE = "OutOfService"
    CLEANING = "Cleaning"


@dataclass
class Customer:
    id: int
    name: str
    email: str
    phone: str

@dataclass
class Agent:
    id: int
    name: str
    branch: str

@dataclass
class VehicleClass:
    """Represents a vehicle class (e.g., Economy, Compact, SUV)."""
    name: str
    base_rate: Money
    daily_mileage_allowance: int = 200  # kilometers per day

@dataclass
class Vehicle:
    """Represents a physical vehicle in the fleet."""
    id: int
    vehicle_class: VehicleClass
    location: 'Location'
    status: VehicleStatus
    odometer: Kilometers
    fuel_level: FuelLevel
    
    def can_be_assigned(self) -> bool:
        """Check if vehicle can be assigned for rental."""
        return self.status == VehicleStatus.AVAILABLE
    
    def mark_as_rented(self) -> None:
        """Mark vehicle as rented."""
        if not self.can_be_assigned():
            raise ValueError(f"Vehicle {self.id} cannot be assigned, current status: {self.status}")
        self.status = VehicleStatus.RENTED
    
    def mark_as_available(self) -> None:
        """Mark vehicle as available."""
        self.status = VehicleStatus.AVAILABLE
    
    def mark_as_out_of_service(self) -> None:
        """Mark vehicle as out of service for maintenance."""
        self.status = VehicleStatus.OUT_OF_SERVICE
    
    def mark_as_cleaning(self) -> None:
        """Mark vehicle as being cleaned."""
        self.status = VehicleStatus.CLEANING

@dataclass
class Location:
    """Represents a branch location."""
    id: int
    name: str
    address: str

@dataclass
class AddOn:
    """Represents an add-on service (e.g., GPS, ChildSeat, ExtraDriver)."""
    name: str
    daily_fee: Money

@dataclass
class InsuranceTier:
    """Represents an insurance coverage tier."""
    name: str
    daily_fee: Money

@dataclass
class Reservation:
    """Represents a customer reservation."""
    id: int
    customer: Customer
    vehicle_class: VehicleClass
    location: Location
    pickup_time: datetime
    return_time: datetime
    addons: List[AddOn] = field(default_factory=list)
    insurance_tier: Optional[InsuranceTier] = None
    deposit: Money = field(default_factory=lambda: Money.zero())
    
    def duration_in_days(self) -> int:
        """Calculate the reservation duration in days (rounded up)."""
        duration = self.return_time - self.pickup_time
        return max(1, (duration.days + (1 if duration.seconds > 0 else 0)))

@dataclass
class RentalAgreement:
    """Represents an active or completed rental."""
    id: int
    reservation: Reservation
    vehicle: Vehicle
    pickup_token: str
    start_odometer: Kilometers
    start_fuel_level: FuelLevel
    pickup_time: datetime
    expected_return_time: datetime
    pickup_agent: Optional['Agent'] = None
    return_agent: Optional['Agent'] = None
    actual_return_time: Optional[datetime] = None
    end_odometer: Optional[Kilometers] = None
    end_fuel_level: Optional[FuelLevel] = None
    charge_items: List['ChargeItem'] = field(default_factory=list)
    is_completed: bool = False
    is_upgraded: bool = False  # Track if customer received an upgrade
    
    def is_overdue(self, current_time: datetime, grace_period_hours: int = 1) -> bool:
        """Check if rental is currently overdue (not yet returned and past grace period)."""
        if self.actual_return_time:
            return False  # Already returned
        from datetime import timedelta
        grace_deadline = self.expected_return_time + timedelta(hours=grace_period_hours)
        return current_time > grace_deadline
    
    def was_returned_late(self, grace_period_hours: int = 1) -> bool:
        """Check if rental was returned late (after grace period)."""
        if not self.actual_return_time:
            return False  # Not yet returned
        from datetime import timedelta
        grace_deadline = self.expected_return_time + timedelta(hours=grace_period_hours)
        return self.actual_return_time > grace_deadline
    
    def calculate_late_hours(self, current_time: datetime, grace_period_hours: int = 1) -> int:
        """Calculate hours late beyond grace period for a given time."""
        from datetime import timedelta
        grace_deadline = self.expected_return_time + timedelta(hours=grace_period_hours)
        
        # If time is before or at grace deadline, no late fees
        if current_time <= grace_deadline:
            return 0
        
        late_duration = current_time - grace_deadline
        total_seconds = late_duration.total_seconds()
        hours = int(total_seconds / 3600)
        # Round up if there are remaining seconds
        if total_seconds % 3600 > 0:
            hours += 1
        return hours
    
    def driven_distance(self) -> Optional[Kilometers]:
        """Calculate distance driven."""
        if self.end_odometer is None:
            return None
        return self.end_odometer - self.start_odometer
    
    def add_charge(self, charge_item: 'ChargeItem') -> None:
        """Add a charge item to the rental."""
        self.charge_items.append(charge_item)
    
    def total_charges(self) -> Money:
        """Calculate total charges."""
        if not self.charge_items:
            return Money.zero()
        return sum((item.amount for item in self.charge_items), Money.zero())

@dataclass
class MaintenanceRecord:
    """Represents a maintenance service record for a vehicle."""
    id: int
    vehicle: Vehicle
    service_type: str
    odometer_threshold: Kilometers
    time_threshold: Optional[datetime] = None
    last_service_date: Optional[datetime] = None
    last_service_odometer: Optional[Kilometers] = None
    
    def is_due(self, current_odometer: Kilometers, current_time: datetime, 
               threshold_km: int = 500) -> bool:
        """
        Check if maintenance is due.
        
        Args:
            current_odometer: Current vehicle odometer reading
            current_time: Current datetime
            threshold_km: How many km before threshold to consider due (default 500)
        
        Returns:
            True if maintenance is due, False otherwise
        """
        # Check odometer threshold
        if current_odometer >= self.odometer_threshold - Kilometers(threshold_km):
            return True
        
        # Check time threshold
        if self.time_threshold and current_time >= self.time_threshold:
            return True
        
        return False

@dataclass
class ChargeItem:
    """Value object representing an itemized charge."""
    description: str
    amount: Money

@dataclass
class Invoice:
    """Represents a billing invoice for a rental."""
    id: int
    rental_agreement: RentalAgreement
    charge_items: List[ChargeItem]
    total_amount: Money
    status: str  # "Pending", "Paid", "Failed"
    created_at: datetime
    
    @classmethod
    def from_rental_agreement(cls, invoice_id: int, rental_agreement: RentalAgreement, 
                             created_at: datetime) -> 'Invoice':
        """Create an invoice from a rental agreement."""
        return cls(
            id=invoice_id,
            rental_agreement=rental_agreement,
            charge_items=rental_agreement.charge_items,
            total_amount=rental_agreement.total_charges(),
            status="Pending",
            created_at=created_at
        )

@dataclass
class Payment:
    """Represents a payment transaction."""
    id: int
    invoice: Invoice
    amount: Money
    status: str  # "Authorized", "Captured", "Failed"
    timestamp: datetime

@dataclass
class Notification:
    """Represents a notification to be sent."""
    type: str  # "ReservationConfirmation", "PickupReminder", "OverdueReturn", "InvoiceSuccess", "InvoiceFailed"
    recipient: str  # email or phone
    message: str
    timestamp: datetime