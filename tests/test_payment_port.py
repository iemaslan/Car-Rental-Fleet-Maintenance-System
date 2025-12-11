import unittest
from adapters.payment_port import PaymentPort

class TestPaymentPort(unittest.TestCase):
    def setUp(self):
        self.payment_port = PaymentPort()

    def test_process_payment_success(self):
        result = self.payment_port.process_payment(invoice_id=1, amount=100.0, success=True)
        self.assertTrue(result)
        self.assertEqual(len(self.payment_port.transactions), 1)
        self.assertEqual(self.payment_port.transactions[0]["status"], "Success")
        self.assertEqual(self.payment_port.transactions[0]["amount"], 100.0)

    def test_process_payment_failure(self):
        result = self.payment_port.process_payment(invoice_id=2, amount=50.0, success=False)
        self.assertFalse(result)
        self.assertEqual(len(self.payment_port.transactions), 1)
        self.assertEqual(self.payment_port.transactions[0]["status"], "Failure")
        self.assertEqual(self.payment_port.transactions[0]["amount"], 50.0)

    def test_list_transactions(self):
        self.payment_port.process_payment(invoice_id=1, amount=100.0, success=True)
        self.payment_port.process_payment(invoice_id=2, amount=50.0, success=False)
        transactions = self.payment_port.list_transactions()
        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0]["status"], "Success")
        self.assertEqual(transactions[1]["status"], "Failure")

if __name__ == "__main__":
    unittest.main()