"""
Notification port and in-memory adapter.
Defines the interface for sending notifications and provides a test implementation.
"""
from abc import ABC, abstractmethod
from typing import List
from domain.models import Notification
from domain.clock import Clock


class NotificationPort(ABC):
    """Abstract port for notification services."""
    
    @abstractmethod
    def send_notification(self, notification: Notification) -> bool:
        """
        Send a notification.
        
        Args:
            notification: The notification to send
            
        Returns:
            True if successful, False otherwise
        """
        pass


class InMemoryNotificationAdapter(NotificationPort):
    """In-memory adapter for testing notification functionality."""
    
    def __init__(self, clock: Clock):
        self.clock = clock
        self.sent_notifications: List[Notification] = []

    def send_notification(self, notification: Notification) -> bool:
        """
        Record a notification in memory.
        
        Args:
            notification: The notification to send
            
        Returns:
            Always True for successful recording
        """
        self.sent_notifications.append(notification)
        print(f"[{notification.timestamp.isoformat()}] Notification sent: {notification.type} to {notification.recipient}")
        print(f"  Message: {notification.message}")
        return True

    def list_notifications(self) -> List[Notification]:
        """
        Get all sent notifications.
        
        Returns:
            List of sent notifications
        """
        return self.sent_notifications.copy()
    
    def get_notifications_by_type(self, notification_type: str) -> List[Notification]:
        """
        Get notifications of a specific type.
        
        Args:
            notification_type: The notification type to filter by
            
        Returns:
            List of matching notifications
        """
        return [n for n in self.sent_notifications if n.type == notification_type]
    
    def get_notifications_by_recipient(self, recipient: str) -> List[Notification]:
        """
        Get notifications for a specific recipient.
        
        Args:
            recipient: The recipient to filter by
            
        Returns:
            List of matching notifications
        """
        return [n for n in self.sent_notifications if n.recipient == recipient]
    
    def clear_notifications(self) -> None:
        """Clear all recorded notifications."""
        self.sent_notifications.clear()