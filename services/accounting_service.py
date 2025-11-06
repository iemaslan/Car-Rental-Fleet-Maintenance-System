"""
Accounting service for managing invoices and payments.
"""
from typing import List, Dict
from domain.models import Invoice, Payment, RentalAgreement, Notification
from domain.value_objects import Money
from domain.clock import Clock
from adapters.payment_port import PaymentPort
from adapters.notification_port import NotificationPort


class AccountingService:
    """Service for managing billing and payments."""
    
    def __init__(self, clock: Clock, payment_port: PaymentPort, 
                 notification_port: NotificationPort):
        self.clock = clock
        self.payment_port = payment_port
        self.notification_port = notification_port
        self.invoices: Dict[int, Invoice] = {}
        self.next_id = 1

    def create_invoice(self, rental_agreement: RentalAgreement) -> Invoice:
        """
        Create an invoice from a completed rental agreement.
        
        Args:
            rental_agreement: The rental agreement to invoice
            
        Returns:
            The created invoice
        """
        invoice = Invoice.from_rental_agreement(
            invoice_id=self.next_id,
            rental_agreement=rental_agreement,
            created_at=self.clock.now()
        )
        self.next_id += 1
        self.invoices[invoice.id] = invoice
        return invoice

    def authorize_deposit(self, invoice: Invoice, amount: Money) -> Payment:
        """
        Pre-authorize a deposit at pickup.
        
        Args:
            invoice: The invoice for the deposit
            amount: The deposit amount
            
        Returns:
            Payment object with authorization result
        """
        payment = self.payment_port.authorize_payment(invoice, amount)
        
        if payment.status == "Authorized":
            print(f"Deposit authorized: {amount} for invoice {invoice.id}")
        else:
            print(f"Deposit authorization failed for invoice {invoice.id}")
            self._send_payment_failure_notification(invoice)
        
        return payment

    def finalize_payment(self, invoice: Invoice) -> bool:
        """
        Finalize payment at return.
        Attempts to charge the total amount.
        
        Args:
            invoice: The invoice to finalize
            
        Returns:
            True if payment successful, False otherwise
        """
        payment = self.payment_port.process_payment(invoice, invoice.total_amount)
        
        if payment.status == "Captured":
            invoice.status = "Paid"
            self._send_payment_success_notification(invoice)
            return True
        else:
            invoice.status = "Failed"
            self._send_payment_failure_notification(invoice)
            return False

    def mark_invoice_pending(self, invoice_id: int) -> bool:
        """
        Mark an invoice as pending when payment fails.
        
        Args:
            invoice_id: The invoice ID
            
        Returns:
            True if invoice found and marked, False otherwise
        """
        invoice = self.invoices.get(invoice_id)
        if not invoice:
            return False
        
        invoice.status = "Pending"
        self._send_payment_failure_notification(invoice)
        return True

    def list_pending_invoices(self) -> List[Invoice]:
        """
        List all invoices with pending status.
        
        Returns:
            List of pending invoices
        """
        return [inv for inv in self.invoices.values() if inv.status == "Pending"]
    
    def list_paid_invoices(self) -> List[Invoice]:
        """
        List all paid invoices.
        
        Returns:
            List of paid invoices
        """
        return [inv for inv in self.invoices.values() if inv.status == "Paid"]
    
    def get_invoice(self, invoice_id: int) -> Invoice:
        """
        Get an invoice by ID.
        
        Args:
            invoice_id: The invoice ID
            
        Returns:
            The invoice, or None if not found
        """
        return self.invoices.get(invoice_id)
    
    def retry_payment(self, invoice_id: int) -> bool:
        """
        Retry payment for a pending invoice.
        
        Args:
            invoice_id: The invoice ID
            
        Returns:
            True if payment successful, False otherwise
        """
        invoice = self.invoices.get(invoice_id)
        if not invoice or invoice.status != "Pending":
            return False
        
        return self.finalize_payment(invoice)
    
    def _send_payment_success_notification(self, invoice: Invoice) -> None:
        """Send payment success notification."""
        customer = invoice.rental_agreement.reservation.customer
        
        message = (
            f"Payment Successful!\n"
            f"Invoice ID: {invoice.id}\n"
            f"Amount: {invoice.total_amount}\n"
            f"Your rental has been completed and paid in full.\n"
            f"Thank you for your business!"
        )
        
        notification = Notification(
            type="InvoiceSuccess",
            recipient=customer.email,
            message=message,
            timestamp=self.clock.now()
        )
        self.notification_port.send_notification(notification)
    
    def _send_payment_failure_notification(self, invoice: Invoice) -> None:
        """Send payment failure notification."""
        customer = invoice.rental_agreement.reservation.customer
        
        message = (
            f"Payment Failed!\n"
            f"Invoice ID: {invoice.id}\n"
            f"Amount: {invoice.total_amount}\n"
            f"We were unable to process your payment.\n"
            f"Please contact us to resolve this issue."
        )
        
        notification = Notification(
            type="InvoiceFailed",
            recipient=customer.email,
            message=message,
            timestamp=self.clock.now()
        )
        self.notification_port.send_notification(notification)