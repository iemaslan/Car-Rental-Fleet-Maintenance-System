import unittest
from domain.models import Invoice, Payment, RentalAgreement
from services.accounting_service import AccountingService

class TestAccountingService(unittest.TestCase):
    def setUp(self):
        self.accounting_service = AccountingService()
        self.invoice = Invoice(
            id=1,
            rental_agreement=RentalAgreement(
                id=1,
                reservation=None,
                vehicle=None,
                start_odometer=0,
                start_fuel_level=0.0
            ),
            total_amount=200.0,
            status="Pending"
        )
        self.accounting_service.invoices.append(self.invoice)

    def test_capture_deposit(self):
        result = self.accounting_service.capture_deposit(invoice=self.invoice, amount=100.0)
        self.assertTrue(result)
        self.assertEqual(len(self.accounting_service.payments), 1)
        self.assertEqual(self.accounting_service.payments[0].status, "Captured")

    def test_finalize_invoice(self):
        self.accounting_service.capture_deposit(invoice=self.invoice, amount=200.0)
        result = self.accounting_service.finalize_invoice(invoice=self.invoice)
        self.assertTrue(result)
        self.assertEqual(self.invoice.status, "Paid")

    def test_list_pending_invoices(self):
        pending_invoices = self.accounting_service.list_pending_invoices()
        self.assertEqual(len(pending_invoices), 1)
        self.assertEqual(pending_invoices[0].id, 1)

if __name__ == "__main__":
    unittest.main()