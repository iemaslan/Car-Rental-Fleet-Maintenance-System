import unittest
from adapters.notification_port import NotificationPort

class TestNotificationPort(unittest.TestCase):
    def setUp(self):
        self.notification_port = NotificationPort()

    def test_send_notification(self):
        self.notification_port.send_notification("Reservation Confirmation", "Your reservation is confirmed.")
        self.assertEqual(len(self.notification_port.sent_notifications), 1)
        self.assertEqual(self.notification_port.sent_notifications[0]["type"], "Reservation Confirmation")
        self.assertEqual(self.notification_port.sent_notifications[0]["message"], "Your reservation is confirmed.")

    def test_list_notifications(self):
        self.notification_port.send_notification("Reminder", "Your pickup is scheduled for tomorrow.")
        self.notification_port.send_notification("Invoice", "Your invoice is ready.")
        notifications = self.notification_port.list_notifications()
        self.assertEqual(len(notifications), 2)
        self.assertEqual(notifications[0]["type"], "Reminder")
        self.assertEqual(notifications[1]["type"], "Invoice")

if __name__ == "__main__":
    unittest.main()