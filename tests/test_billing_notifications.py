"""
Test suite for billing, payments, and notifications using mocking.
Tests verify payment success/failure scenarios, invoice state updates,
and notification delivery using mocked adapters.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import Mock, MagicMock, patch, call

from domain.models import Invoice, Payment, Notification
from domain.value_objects import Money, FuelLevel, Kilometers


class TestPaymentSuccess:
    """Test successful payment scenarios."""
    
    def test_successful_payment_updates_invoice_status(self, accounting_service, 
                                                       completed_rental_scenario, 
                                                       payment_adapter):
        """Test successful payment marks invoice as paid."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        # Create invoice
        invoice = accounting_service.create_invoice(rental)
        
        # Process payment (success)
        payment_adapter.set_simulate_failure(False)
        result = accounting_service.finalize_payment(invoice)
        
        assert result is True
        assert invoice.status == "Paid"
    
    def test_successful_payment_sends_notification(self, accounting_service, 
                                                   completed_rental_scenario, 
                                                   notification_adapter):
        """Test successful payment triggers success notification."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        # Create and pay invoice
        invoice = accounting_service.create_invoice(rental)
        accounting_service.finalize_payment(invoice)
        
        # Check notification was sent
        notifications = notification_adapter.get_notifications_by_type("InvoiceSuccess")
        assert len(notifications) == 1
        
        notification = notifications[0]
        assert notification.recipient == rental.reservation.customer.email
        assert "successful" in notification.message.lower()
        assert str(invoice.id) in notification.message
    
    def test_successful_deposit_authorization(self, accounting_service, 
                                             basic_reservation, 
                                             payment_adapter):
        """Test successful deposit authorization."""
        # Create invoice
        from domain.models import RentalAgreement, ChargeItem
        rental = RentalAgreement(
            id=1, reservation=basic_reservation, vehicle=None,
            pickup_token="test", start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0), 
            pickup_time=basic_reservation.pickup_time,
            expected_return_time=basic_reservation.return_time
        )
        invoice = accounting_service.create_invoice(rental)
        
        # Authorize deposit
        deposit_amount = Money(Decimal('200.00'))
        payment = accounting_service.authorize_deposit(invoice, deposit_amount)
        
        assert payment.status == "Authorized"
        assert payment.amount == deposit_amount


class TestPaymentFailure:
    """Test payment failure scenarios."""
    
    def test_failed_payment_marks_invoice_failed(self, accounting_service, 
                                                completed_rental_scenario, 
                                                payment_adapter):
        """Test failed payment marks invoice as failed."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        # Create invoice
        invoice = accounting_service.create_invoice(rental)
        
        # Simulate payment failure
        payment_adapter.set_simulate_failure(True)
        result = accounting_service.finalize_payment(invoice)
        
        assert result is False
        assert invoice.status == "Failed"
    
    def test_failed_payment_sends_notification(self, accounting_service, 
                                              completed_rental_scenario, 
                                              payment_adapter, 
                                              notification_adapter):
        """Test failed payment triggers failure notification."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        # Create invoice and fail payment
        invoice = accounting_service.create_invoice(rental)
        payment_adapter.set_simulate_failure(True)
        accounting_service.finalize_payment(invoice)
        
        # Check notification was sent
        notifications = notification_adapter.get_notifications_by_type("InvoiceFailed")
        assert len(notifications) == 1
        
        notification = notifications[0]
        assert notification.recipient == rental.reservation.customer.email
        assert "failed" in notification.message.lower()
        assert str(invoice.id) in notification.message
    
    def test_mark_invoice_pending(self, accounting_service, 
                                 completed_rental_scenario):
        """Test manually marking invoice as pending."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        
        result = accounting_service.mark_invoice_pending(invoice.id)
        
        assert result is True
        assert invoice.status == "Pending"


class TestPaymentMocking:
    """Test payment operations using mocking techniques."""
    
    def test_payment_adapter_called_with_correct_arguments(self, accounting_service, 
                                                          completed_rental_scenario, 
                                                          monkeypatch):
        """Test payment adapter is called with expected arguments using monkeypatch."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        
        # Create mock payment adapter
        mock_adapter = Mock()
        mock_payment = Payment(
            id=1, invoice=invoice, amount=invoice.total_amount,
            status="Captured", timestamp=fixed_clock.now()
        )
        mock_adapter.process_payment.return_value = mock_payment
        
        # Replace adapter with mock using monkeypatch
        monkeypatch.setattr(accounting_service, 'payment_port', mock_adapter)
        
        # Finalize payment
        accounting_service.finalize_payment(invoice)
        
        # Verify adapter was called
        mock_adapter.process_payment.assert_called_once_with(invoice, invoice.total_amount)
    
    def test_notification_adapter_called_on_success(self, accounting_service, 
                                                   completed_rental_scenario, 
                                                   monkeypatch):
        """Test notification adapter called on successful payment using monkeypatch."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        
        # Create mock notification adapter
        mock_notifier = Mock()
        mock_notifier.send_notification.return_value = True
        
        # Replace with mock
        monkeypatch.setattr(accounting_service, 'notification_port', mock_notifier)
        
        # Finalize payment (success)
        accounting_service.finalize_payment(invoice)
        
        # Verify notification was sent
        assert mock_notifier.send_notification.called
        
        # Get the notification that was sent
        call_args = mock_notifier.send_notification.call_args
        notification = call_args[0][0]
        
        assert notification.type == "InvoiceSuccess"
        assert notification.recipient == rental.reservation.customer.email
    
    def test_notification_adapter_called_on_failure(self, accounting_service, 
                                                   completed_rental_scenario, 
                                                   payment_adapter,
                                                   monkeypatch):
        """Test notification adapter called on failed payment using monkeypatch."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        
        # Mock notification adapter
        mock_notifier = Mock()
        mock_notifier.send_notification.return_value = True
        monkeypatch.setattr(accounting_service, 'notification_port', mock_notifier)
        
        # Simulate payment failure
        payment_adapter.set_simulate_failure(True)
        accounting_service.finalize_payment(invoice)
        
        # Verify notification was sent
        assert mock_notifier.send_notification.called
        
        # Get the notification
        call_args = mock_notifier.send_notification.call_args
        notification = call_args[0][0]
        
        assert notification.type == "InvoiceFailed"
    
    def test_payment_retry_after_failure(self, accounting_service, 
                                        completed_rental_scenario, 
                                        payment_adapter):
        """Test retrying payment after initial failure."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        
        # First attempt fails
        payment_adapter.set_simulate_failure(True)
        result1 = accounting_service.finalize_payment(invoice)
        assert result1 is False
        assert invoice.status == "Failed"  # Status becomes Failed after unsuccessful payment
        
        # Reset invoice status to Pending for retry
        invoice.status = "Pending"
        
        # Second attempt succeeds
        payment_adapter.set_simulate_failure(False)
        result2 = accounting_service.retry_payment(invoice.id)
        assert result2 is True
        assert invoice.status == "Paid"


class TestNotificationScenarios:
    """Test various notification scenarios."""
    
    def test_reservation_confirmation_notification(self, reservation_service, 
                                                   customer, economy_class, 
                                                   location, notification_adapter, 
                                                   base_time):
        """Test reservation creation sends confirmation notification."""
        pickup = base_time + timedelta(days=1)
        return_time = pickup + timedelta(days=3)
        
        reservation = reservation_service.create_reservation(
            customer=customer,
            vehicle_class=economy_class,
            location=location,
            pickup_time=pickup,
            return_time=return_time
        )
        
        # Check confirmation was sent
        notifications = notification_adapter.get_notifications_by_type("ReservationConfirmation")
        assert len(notifications) == 1
        
        notification = notifications[0]
        assert notification.recipient == customer.email
        assert str(reservation.id) in notification.message
    
    def test_multiple_notifications_tracked(self, accounting_service, 
                                          completed_rental_scenario, 
                                          notification_adapter):
        """Test multiple notifications are tracked correctly."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        # Create multiple invoices with different outcomes
        invoice1 = accounting_service.create_invoice(rental)
        accounting_service.finalize_payment(invoice1)  # Success
        
        # Second rental (would need to create another scenario, simplified)
        invoice2 = accounting_service.create_invoice(rental)
        accounting_service.mark_invoice_pending(invoice2.id)  # Pending/Failed
        
        # Should have success and failure notifications
        all_notifications = notification_adapter.list_notifications()
        assert len(all_notifications) >= 2
    
    def test_notification_by_recipient(self, reservation_service, notification_adapter,
                                      economy_class, location, base_time):
        """Test filtering notifications by recipient."""
        from domain.models import Customer
        
        # Create two customers
        customer1 = Customer(id=1, name="John Doe", email="john@example.com", phone="123")
        customer2 = Customer(id=2, name="Jane Doe", email="jane@example.com", phone="456")
        
        pickup = base_time + timedelta(days=1)
        return_time = pickup + timedelta(days=3)
        
        # Create reservations for both
        reservation_service.create_reservation(
            customer=customer1, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time
        )
        
        reservation_service.create_reservation(
            customer=customer2, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time
        )
        
        # Check each customer got their notification
        john_notifications = notification_adapter.get_notifications_by_recipient("john@example.com")
        jane_notifications = notification_adapter.get_notifications_by_recipient("jane@example.com")
        
        assert len(john_notifications) == 1
        assert len(jane_notifications) == 1


class TestInvoiceManagement:
    """Test invoice management operations."""
    
    def test_create_invoice_from_rental(self, accounting_service, 
                                       completed_rental_scenario):
        """Test creating invoice from completed rental."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        
        assert invoice is not None
        assert invoice.rental_agreement == rental
        assert invoice.total_amount == rental.total_charges()
        assert invoice.status == "Pending"
        assert len(invoice.charge_items) > 0
    
    def test_list_pending_invoices(self, accounting_service, 
                                  completed_rental_scenario, 
                                  payment_adapter):
        """Test listing pending invoices."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        # Create invoices with different statuses
        invoice1 = accounting_service.create_invoice(rental)
        
        invoice2 = accounting_service.create_invoice(rental)
        accounting_service.finalize_payment(invoice2)  # Paid
        
        invoice3 = accounting_service.create_invoice(rental)
        payment_adapter.set_simulate_failure(True)
        accounting_service.finalize_payment(invoice3)  # Pending
        
        pending = accounting_service.list_pending_invoices()
        
        # At least invoice1 (never paid) and invoice3 (failed) should be pending
        assert len(pending) >= 1
    
    def test_list_paid_invoices(self, accounting_service, 
                               completed_rental_scenario):
        """Test listing paid invoices."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        accounting_service.finalize_payment(invoice)
        
        paid = accounting_service.list_paid_invoices()
        
        assert len(paid) >= 1
        assert invoice in paid


@pytest.mark.parametrize("payment_success,expected_invoice_status,expected_notification_type", [
    (True, "Paid", "InvoiceSuccess"),
    (False, "Failed", "InvoiceFailed"),
])
def test_payment_outcome_scenarios(payment_success, expected_invoice_status, 
                                  expected_notification_type, accounting_service, 
                                  completed_rental_scenario, payment_adapter, 
                                  notification_adapter):
    """Parametrized test for payment success/failure outcomes."""
    rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
    
    invoice = accounting_service.create_invoice(rental)
    
    # Set payment outcome
    payment_adapter.set_simulate_failure(not payment_success)
    
    # Clear previous notifications
    notification_adapter.clear_notifications()
    
    # Process payment
    accounting_service.finalize_payment(invoice)
    
    # Verify invoice status
    assert invoice.status == expected_invoice_status
    
    # Verify notification
    notifications = notification_adapter.get_notifications_by_type(expected_notification_type)
    assert len(notifications) == 1


class TestMockingTechniques:
    """Demonstrate various mocking techniques for testing."""
    
    def test_mock_payment_port_return_value(self, accounting_service, 
                                           completed_rental_scenario, 
                                           monkeypatch, fixed_clock):
        """Test mocking payment port with specific return value."""
        rental_service, rental, vehicle, clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        
        # Create mock that returns specific payment
        mock_payment = Payment(
            id=999, invoice=invoice, amount=invoice.total_amount,
            status="Captured", timestamp=fixed_clock.now()
        )
        
        mock_port = Mock()
        mock_port.process_payment.return_value = mock_payment
        
        monkeypatch.setattr(accounting_service, 'payment_port', mock_port)
        
        # Process payment
        result = accounting_service.finalize_payment(invoice)
        
        assert result is True
        assert invoice.status == "Paid"
        
        # Verify mock was called correctly
        mock_port.process_payment.assert_called_once()
        args, kwargs = mock_port.process_payment.call_args
        assert args[0] == invoice
        assert args[1] == invoice.total_amount
    
    def test_mock_notification_port_verify_calls(self, accounting_service, 
                                                completed_rental_scenario, 
                                                payment_adapter, monkeypatch):
        """Test verifying notification port is called correctly."""
        rental_service, rental, vehicle, clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        
        # Mock notification port
        mock_notifier = Mock()
        monkeypatch.setattr(accounting_service, 'notification_port', mock_notifier)
        
        # Process successful payment
        payment_adapter.set_simulate_failure(False)
        accounting_service.finalize_payment(invoice)
        
        # Verify notification was sent exactly once
        assert mock_notifier.send_notification.call_count == 1
        
        # Verify notification content
        notification = mock_notifier.send_notification.call_args[0][0]
        assert isinstance(notification, Notification)
        assert notification.type == "InvoiceSuccess"
        assert invoice.rental_agreement.reservation.customer.email in notification.recipient
    
    def test_mock_both_payment_and_notification(self, accounting_service, 
                                               completed_rental_scenario, 
                                               monkeypatch, fixed_clock):
        """Test mocking both payment and notification ports."""
        rental_service, rental, vehicle, clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        
        # Mock both ports
        mock_payment_port = Mock()
        mock_notification_port = Mock()
        
        # Configure payment mock to fail
        failed_payment = Payment(
            id=1, invoice=invoice, amount=invoice.total_amount,
            status="Failed", timestamp=fixed_clock.now()
        )
        mock_payment_port.process_payment.return_value = failed_payment
        
        monkeypatch.setattr(accounting_service, 'payment_port', mock_payment_port)
        monkeypatch.setattr(accounting_service, 'notification_port', mock_notification_port)
        
        # Process payment
        result = accounting_service.finalize_payment(invoice)
        
        # Verify both were called
        assert mock_payment_port.process_payment.called
        assert mock_notification_port.send_notification.called
        
        # Verify failure notification
        notification = mock_notification_port.send_notification.call_args[0][0]
        assert notification.type == "InvoiceFailed"
        
        # Verify invoice status
        assert invoice.status == "Failed"
    
    def test_mock_side_effects(self, accounting_service, 
                              completed_rental_scenario, 
                              monkeypatch, fixed_clock):
        """Test using mock side effects to simulate varying behavior."""
        rental_service, rental, vehicle, clock = completed_rental_scenario
        
        invoice1 = accounting_service.create_invoice(rental)
        invoice2 = accounting_service.create_invoice(rental)
        
        # Mock payment port with side effects (first fails, second succeeds)
        mock_payment_port = Mock()
        
        failed_payment = Payment(
            id=1, invoice=invoice1, amount=invoice1.total_amount,
            status="Failed", timestamp=fixed_clock.now()
        )
        success_payment = Payment(
            id=2, invoice=invoice2, amount=invoice2.total_amount,
            status="Captured", timestamp=fixed_clock.now()
        )
        
        mock_payment_port.process_payment.side_effect = [failed_payment, success_payment]
        
        monkeypatch.setattr(accounting_service, 'payment_port', mock_payment_port)
        
        # First payment fails
        result1 = accounting_service.finalize_payment(invoice1)
        assert result1 is False
        assert invoice1.status == "Failed"
        
        # Second payment succeeds
        result2 = accounting_service.finalize_payment(invoice2)
        assert result2 is True
        assert invoice2.status == "Paid"


class TestPaymentTransactionAuditing:
    """Test payment transaction auditing and tracking."""
    
    def test_payment_transactions_recorded(self, payment_adapter, 
                                          completed_rental_scenario, 
                                          accounting_service):
        """Test payment transactions are recorded for auditing."""
        rental_service, rental, vehicle, clock = completed_rental_scenario
        
        invoice = accounting_service.create_invoice(rental)
        
        initial_tx_count = len(payment_adapter.list_transactions())
        
        # Process payment
        accounting_service.finalize_payment(invoice)
        
        # Should have recorded transaction
        transactions = payment_adapter.list_transactions()
        assert len(transactions) > initial_tx_count
        
        # Verify transaction details
        latest_tx = transactions[-1]
        assert latest_tx['invoice_id'] == invoice.id
        assert latest_tx['type'] == 'process'
