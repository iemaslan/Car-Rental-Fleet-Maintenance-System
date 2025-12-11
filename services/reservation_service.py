"""
Reservation service for managing customer reservations.
"""
from typing import List, Optional, Dict
from domain.models import Reservation, Customer, VehicleClass, Location, AddOn, InsuranceTier, Notification
from domain.value_objects import Money
from domain.clock import Clock
from adapters.notification_port import NotificationPort


class ReservationService:
    """Service for managing reservations."""
    
    def __init__(self, clock: Clock, notification_port: NotificationPort):
        self.clock = clock
        self.notification_port = notification_port
        self.reservations: Dict[int, Reservation] = {}
        self.next_id = 1

    def create_reservation(self, customer: Customer, vehicle_class: VehicleClass, 
                          location: Location, pickup_time, return_time,
                          addons: List[AddOn] = None, 
                          insurance_tier: Optional[InsuranceTier] = None, 
                          deposit: Money = None) -> Reservation:
        """
        Create a new reservation.
        
        Args:
            customer: The customer making the reservation
            vehicle_class: The class of vehicle requested
            location: The pickup/return location
            pickup_time: Pickup datetime
            return_time: Return datetime
            addons: List of add-on services
            insurance_tier: Insurance coverage tier
            deposit: Deposit amount
            
        Returns:
            The created reservation
        """
        if addons is None:
            addons = []
        if deposit is None:
            deposit = Money.zero()
        
        reservation = Reservation(
            id=self.next_id,
            customer=customer,
            vehicle_class=vehicle_class,
            location=location,
            pickup_time=pickup_time,
            return_time=return_time,
            addons=addons,
            insurance_tier=insurance_tier,
            deposit=deposit
        )
        self.next_id += 1
        self.reservations[reservation.id] = reservation
        
        # Send confirmation notification
        self._send_reservation_confirmation(reservation)
        
        return reservation

    def modify_reservation(self, reservation_id: int, 
                          pickup_time=None,
                          return_time=None,
                          addons: List[AddOn] = None,
                          insurance_tier: Optional[InsuranceTier] = None) -> Reservation:
        """
        Modify an existing reservation.
        
        Args:
            reservation_id: The reservation ID
            pickup_time: New pickup datetime (optional)
            return_time: New return datetime (optional)
            addons: New list of add-ons (optional)
            insurance_tier: New insurance tier (optional)
            
        Returns:
            The modified reservation
            
        Raises:
            ValueError: If reservation not found
        """
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            raise ValueError(f"Reservation {reservation_id} not found")
        
        if pickup_time is not None:
            reservation.pickup_time = pickup_time
        if return_time is not None:
            reservation.return_time = return_time
        if addons is not None:
            reservation.addons = addons
        if insurance_tier is not None:
            reservation.insurance_tier = insurance_tier
        
        # Send modification notification
        self._send_reservation_modification(reservation)
        
        return reservation

    def cancel_reservation(self, reservation_id: int) -> bool:
        """
        Cancel a reservation.
        
        Args:
            reservation_id: The reservation ID
            
        Returns:
            True if cancelled, False if not found
        """
        reservation = self.reservations.pop(reservation_id, None)
        if reservation:
            # Send cancellation notification
            notification = Notification(
                type="ReservationCancellation",
                recipient=reservation.customer.email,
                message=f"Your reservation #{reservation.id} has been cancelled.",
                timestamp=self.clock.now()
            )
            self.notification_port.send_notification(notification)
            return True
        return False

    def get_reservation(self, reservation_id: int) -> Optional[Reservation]:
        """Get a reservation by ID."""
        return self.reservations.get(reservation_id)

    def list_reservations(self) -> List[Reservation]:
        """List all reservations."""
        return list(self.reservations.values())
    
    def list_customer_reservations(self, customer_id: int) -> List[Reservation]:
        """List all reservations for a customer."""
        return [r for r in self.reservations.values() if r.customer.id == customer_id]
    
    def _send_reservation_confirmation(self, reservation: Reservation) -> None:
        """Send reservation confirmation notification."""
        message = (
            f"Reservation confirmed!\n"
            f"Reservation ID: {reservation.id}\n"
            f"Vehicle Class: {reservation.vehicle_class.name}\n"
            f"Location: {reservation.location.name}\n"
            f"Pickup: {reservation.pickup_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"Return: {reservation.return_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"Deposit: {reservation.deposit}"
        )
        
        notification = Notification(
            type="ReservationConfirmation",
            recipient=reservation.customer.email,
            message=message,
            timestamp=self.clock.now()
        )
        self.notification_port.send_notification(notification)
    
    def _send_reservation_modification(self, reservation: Reservation) -> None:
        """Send reservation modification notification."""
        message = (
            f"Reservation modified!\n"
            f"Reservation ID: {reservation.id}\n"
            f"New Pickup: {reservation.pickup_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"New Return: {reservation.return_time.strftime('%Y-%m-%d %H:%M')}"
        )
        
        notification = Notification(
            type="ReservationModification",
            recipient=reservation.customer.email,
            message=message,
            timestamp=self.clock.now()
        )
        self.notification_port.send_notification(notification)
    
    def send_pickup_reminder(self, reservation_id: int) -> bool:
        """
        Send a pickup reminder notification.
        
        Args:
            reservation_id: The reservation ID
            
        Returns:
            True if sent, False if reservation not found
        """
        reservation = self.reservations.get(reservation_id)
        if not reservation:
            return False
        
        message = (
            f"Pickup Reminder!\n"
            f"Your rental is scheduled for pickup tomorrow.\n"
            f"Reservation ID: {reservation.id}\n"
            f"Vehicle Class: {reservation.vehicle_class.name}\n"
            f"Location: {reservation.location.name}\n"
            f"Pickup Time: {reservation.pickup_time.strftime('%Y-%m-%d %H:%M')}"
        )
        
        notification = Notification(
            type="PickupReminder",
            recipient=reservation.customer.email,
            message=message,
            timestamp=self.clock.now()
        )
        self.notification_port.send_notification(notification)
        return True