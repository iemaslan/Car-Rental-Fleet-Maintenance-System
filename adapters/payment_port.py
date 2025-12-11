"""
Payment port and fake adapter.
Defines the interface for payment processing and provides a test implementation.
"""
from abc import ABC, abstractmethod
from typing import List, Dict
from enum import Enum
from domain.models import Payment, Invoice
from domain.value_objects import Money
from domain.clock import Clock


class PaymentStatus(Enum):
    """Payment status enumeration."""
    AUTHORIZED = "Authorized"
    CAPTURED = "Captured"
    FAILED = "Failed"
    REFUNDED = "Refunded"


class PaymentPort(ABC):
    """Abstract port for payment services."""
    
    @abstractmethod
    def authorize_payment(self, invoice: Invoice, amount: Money) -> Payment:
        """
        Authorize a payment (e.g., for deposit).
        
        Args:
            invoice: The invoice for the payment
            amount: The amount to authorize
            
        Returns:
            Payment object with authorization result
        """
        pass
    
    @abstractmethod
    def capture_payment(self, payment: Payment) -> bool:
        """
        Capture a previously authorized payment.
        
        Args:
            payment: The payment to capture
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def process_payment(self, invoice: Invoice, amount: Money) -> Payment:
        """
        Process a direct payment (authorize and capture).
        
        Args:
            invoice: The invoice for the payment
            amount: The amount to charge
            
        Returns:
            Payment object with processing result
        """
        pass


class FakePaymentAdapter(PaymentPort):
    """
    Fake payment adapter for testing.
    Can be configured to simulate success or failure.
    """
    
    def __init__(self, clock: Clock, simulate_failure: bool = False):
        self.clock = clock
        self.simulate_failure = simulate_failure
        self.payments: List[Payment] = []
        self.transactions: List[Dict[str, any]] = []
        self.next_payment_id = 1
    
    def set_simulate_failure(self, simulate_failure: bool) -> None:
        """Configure whether to simulate payment failures."""
        self.simulate_failure = simulate_failure

    def authorize_payment(self, invoice: Invoice, amount: Money) -> Payment:
        """
        Simulate payment authorization.
        
        Args:
            invoice: The invoice for the payment
            amount: The amount to authorize
            
        Returns:
            Payment object with authorization result
        """
        status = PaymentStatus.FAILED if self.simulate_failure else PaymentStatus.AUTHORIZED
        
        payment = Payment(
            id=self.next_payment_id,
            invoice=invoice,
            amount=amount,
            status=status.value,
            timestamp=self.clock.now()
        )
        self.next_payment_id += 1
        
        self.payments.append(payment)
        self._record_transaction(payment, "authorize")
        
        print(f"[{payment.timestamp.isoformat()}] Payment authorization: {status.value}")
        print(f"  Invoice: {invoice.id}, Amount: {amount}")
        
        return payment

    def capture_payment(self, payment: Payment) -> bool:
        """
        Simulate capturing an authorized payment.
        
        Args:
            payment: The payment to capture
            
        Returns:
            True if successful, False otherwise
        """
        if payment.status != PaymentStatus.AUTHORIZED.value:
            print(f"Cannot capture payment {payment.id}: status is {payment.status}")
            return False
        
        if self.simulate_failure:
            payment.status = PaymentStatus.FAILED.value
            self._record_transaction(payment, "capture_failed")
            print(f"Payment capture failed: {payment.id}")
            return False
        
        payment.status = PaymentStatus.CAPTURED.value
        payment.timestamp = self.clock.now()
        self._record_transaction(payment, "capture")
        print(f"Payment captured: {payment.id}, Amount: {payment.amount}")
        return True

    def process_payment(self, invoice: Invoice, amount: Money) -> Payment:
        """
        Simulate direct payment processing.
        
        Args:
            invoice: The invoice for the payment
            amount: The amount to charge
            
        Returns:
            Payment object with processing result
        """
        status = PaymentStatus.FAILED if self.simulate_failure else PaymentStatus.CAPTURED
        
        payment = Payment(
            id=self.next_payment_id,
            invoice=invoice,
            amount=amount,
            status=status.value,
            timestamp=self.clock.now()
        )
        self.next_payment_id += 1
        
        self.payments.append(payment)
        self._record_transaction(payment, "process")
        
        print(f"[{payment.timestamp.isoformat()}] Payment processed: {status.value}")
        print(f"  Invoice: {invoice.id}, Amount: {amount}")
        
        return payment
    
    def _record_transaction(self, payment: Payment, transaction_type: str) -> None:
        """Record a transaction for auditing."""
        transaction = {
            "payment_id": payment.id,
            "invoice_id": payment.invoice.id,
            "amount": str(payment.amount),
            "status": payment.status,
            "type": transaction_type,
            "timestamp": payment.timestamp.isoformat()
        }
        self.transactions.append(transaction)

    def list_payments(self) -> List[Payment]:
        """Get all payments."""
        return self.payments.copy()

    def list_transactions(self) -> List[Dict[str, any]]:
        """Get all transaction records."""
        return self.transactions.copy()
    
    def get_payment_by_id(self, payment_id: int) -> Payment:
        """Get a payment by ID."""
        for payment in self.payments:
            if payment.id == payment_id:
                return payment
        return None