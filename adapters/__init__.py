"""
Adapters package for the Car Rental & Fleet Maintenance System.
Contains port interfaces and adapter implementations for external services.
"""
from .notification_port import NotificationPort, InMemoryNotificationAdapter
from .payment_port import PaymentPort, FakePaymentAdapter, PaymentStatus

__all__ = [
    'NotificationPort',
    'InMemoryNotificationAdapter',
    'PaymentPort',
    'FakePaymentAdapter',
    'PaymentStatus',
]
