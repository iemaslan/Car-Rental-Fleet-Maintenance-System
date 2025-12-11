"""
Domain package for the Car Rental & Fleet Maintenance System.
Contains core business entities, value objects, and domain logic.
"""
from .models import (
    Customer,
    Agent,
    VehicleClass,
    Vehicle,
    VehicleStatus,
    Location,
    AddOn,
    InsuranceTier,
    Reservation,
    RentalAgreement,
    MaintenanceRecord,
    ChargeItem,
    Invoice,
    Payment,
    Notification,
)
from .value_objects import Money, FuelLevel, Kilometers
from .clock import Clock, SystemClock, FixedClock

__all__ = [
    # Entities
    'Customer',
    'Agent',
    'VehicleClass',
    'Vehicle',
    'VehicleStatus',
    'Location',
    'AddOn',
    'InsuranceTier',
    'Reservation',
    'RentalAgreement',
    'MaintenanceRecord',
    'ChargeItem',
    'Invoice',
    'Payment',
    'Notification',
    # Value Objects
    'Money',
    'FuelLevel',
    'Kilometers',
    # Clock
    'Clock',
    'SystemClock',
    'FixedClock',
]
