"""
Rental service for managing vehicle pickups, returns, and rental extensions.
Implements idempotent operations using pickup tokens.
"""
from typing import Dict, Optional, Set
from domain.models import RentalAgreement, Reservation, Vehicle, VehicleStatus, Agent
from domain.value_objects import FuelLevel, Kilometers
from domain.clock import Clock
from domain.audit_log import AuditLogger, AuditEventType
from services.pricing_policy import PricingPolicy
from services.maintenance_service import MaintenanceService
import uuid


class RentalService:
    """Service for managing rental operations."""
    
    def __init__(self, clock: Clock, pricing_policy: PricingPolicy, 
                 maintenance_service: MaintenanceService, audit_logger: AuditLogger):
        self.clock = clock
        self.pricing_policy = pricing_policy
        self.maintenance_service = maintenance_service
        self.audit_logger = audit_logger
        self.rental_agreements: Dict[int, RentalAgreement] = {}
        self.pickup_tokens: Set[str] = set()  # Track used tokens for idempotency
        self.vehicle_rentals: Dict[int, int] = {}  # vehicle_id -> rental_agreement_id
        self.next_id = 1

    def pickup_vehicle(self, reservation: Reservation, vehicle: Vehicle, 
                      start_odometer: Kilometers, start_fuel_level: FuelLevel,
                      agent: Optional[Agent] = None,
                      pickup_token: Optional[str] = None) -> RentalAgreement:
        """
        Perform an idempotent vehicle pickup.
        
        Args:
            reservation: The reservation being fulfilled
            vehicle: The vehicle being picked up
            start_odometer: Odometer reading at pickup
            start_fuel_level: Fuel level at pickup
            agent: The agent performing the pickup
            pickup_token: Optional token for idempotency (generated if not provided)
            
        Returns:
            The rental agreement
            
        Raises:
            ValueError: If vehicle cannot be assigned or pickup fails
        """
        # Generate token if not provided
        if not pickup_token:
            pickup_token = str(uuid.uuid4())
        
        # Check for idempotency - if token already used, return existing rental
        if pickup_token in self.pickup_tokens:
            # Find and return existing rental with this token
            for rental in self.rental_agreements.values():
                if rental.pickup_token == pickup_token:
                    return rental
            # Token exists but rental not found - shouldn't happen, but handle gracefully
            raise ValueError(f"Pickup token {pickup_token} was already used but rental not found")
        
        # Validate vehicle can be assigned
        if not vehicle.can_be_assigned():
            raise ValueError(f"Vehicle {vehicle.id} is not available (status: {vehicle.status.value})")
        
        # Check maintenance status
        if self.maintenance_service.is_maintenance_due(vehicle):
            raise ValueError(f"Vehicle {vehicle.id} is due for maintenance and cannot be assigned")
        
        # Check if this is an upgrade
        is_upgraded = vehicle.vehicle_class.name != reservation.vehicle_class.name
        
        # Create rental agreement
        current_time = self.clock.now()
        rental_agreement = RentalAgreement(
            id=self.next_id,
            reservation=reservation,
            vehicle=vehicle,
            pickup_token=pickup_token,
            start_odometer=start_odometer,
            start_fuel_level=start_fuel_level,
            pickup_time=current_time,
            expected_return_time=reservation.return_time,
            pickup_agent=agent,
            is_upgraded=is_upgraded
        )
        
        self.next_id += 1
        self.rental_agreements[rental_agreement.id] = rental_agreement
        self.pickup_tokens.add(pickup_token)
        self.vehicle_rentals[vehicle.id] = rental_agreement.id
        
        # Update vehicle status
        vehicle.mark_as_rented()
        vehicle.odometer = start_odometer
        vehicle.fuel_level = start_fuel_level
        
        # Log pickup event
        self.audit_logger.log_event(
            timestamp=current_time,
            event_type=AuditEventType.VEHICLE_PICKUP,
            actor_type="Agent" if agent else "System",
            actor_id=agent.id if agent else None,
            actor_name=agent.name if agent else "System",
            entity_type="RentalAgreement",
            entity_id=rental_agreement.id,
            description=f"Vehicle {vehicle.id} picked up for reservation {reservation.id}",
            metadata={
                'vehicle_id': vehicle.id,
                'reservation_id': reservation.id,
                'pickup_token': pickup_token,
                'start_odometer': start_odometer.value,
                'start_fuel_level': start_fuel_level.level
            }
        )
        
        # Log upgrade if applicable
        if is_upgraded:
            self.audit_logger.log_event(
                timestamp=current_time,
                event_type=AuditEventType.VEHICLE_UPGRADE,
                actor_type="Agent" if agent else "System",
                actor_id=agent.id if agent else None,
                actor_name=agent.name if agent else "System",
                entity_type="RentalAgreement",
                entity_id=rental_agreement.id,
                description=f"Vehicle upgraded from {reservation.vehicle_class.name} to {vehicle.vehicle_class.name}",
                metadata={
                    'original_class': reservation.vehicle_class.name,
                    'upgraded_class': vehicle.vehicle_class.name,
                    'vehicle_id': vehicle.id
                }
            )
        
        return rental_agreement

    def return_vehicle(self, rental_agreement_id: int, end_odometer: Kilometers, 
                      end_fuel_level: FuelLevel, agent: Optional[Agent] = None) -> RentalAgreement:
        """
        Process a vehicle return and compute all charges.
        
        Args:
            rental_agreement_id: The rental agreement ID
            end_odometer: Odometer reading at return
            end_fuel_level: Fuel level at return
            agent: The agent processing the return
            
        Returns:
            The updated rental agreement with charges
            
        Raises:
            ValueError: If rental not found or already completed
        """
        rental = self.rental_agreements.get(rental_agreement_id)
        if not rental:
            raise ValueError(f"Rental agreement {rental_agreement_id} not found")
        
        if rental.is_completed:
            # Idempotent - return already exists
            return rental
        
        current_time = self.clock.now()
        
        # Update rental agreement with return information
        rental.actual_return_time = current_time
        rental.end_odometer = end_odometer
        rental.end_fuel_level = end_fuel_level
        rental.return_agent = agent
        
        # Calculate all charges using pricing policy
        charge_items = self.pricing_policy.calculate_charges(rental)
        rental.charge_items = charge_items
        rental.is_completed = True
        
        # Update vehicle status and readings
        rental.vehicle.mark_as_cleaning()  # Needs cleaning before next rental
        rental.vehicle.odometer = end_odometer
        rental.vehicle.fuel_level = end_fuel_level
        
        # Remove from active rentals
        if rental.vehicle.id in self.vehicle_rentals:
            del self.vehicle_rentals[rental.vehicle.id]
        
        # Log return event
        self.audit_logger.log_event(
            timestamp=current_time,
            event_type=AuditEventType.VEHICLE_RETURN,
            actor_type="Agent" if agent else "System",
            actor_id=agent.id if agent else None,
            actor_name=agent.name if agent else "System",
            entity_type="RentalAgreement",
            entity_id=rental.id,
            description=f"Vehicle {rental.vehicle.id} returned for rental agreement {rental.id}",
            metadata={
                'vehicle_id': rental.vehicle.id,
                'end_odometer': end_odometer.value,
                'end_fuel_level': end_fuel_level.level,
                'total_charges': str(rental.total_charges()),
                'driven_distance': rental.driven_distance().value if rental.driven_distance() else 0
            }
        )
        
        return rental

    def extend_rental(self, rental_agreement_id: int, new_return_time) -> bool:
        """
        Extend a rental period if no conflicts exist.
        
        Args:
            rental_agreement_id: The rental agreement ID
            new_return_time: The new expected return datetime
            
        Returns:
            True if extension was successful, False otherwise
            
        Raises:
            ValueError: If rental not found or already completed
        """
        rental = self.rental_agreements.get(rental_agreement_id)
        if not rental:
            raise ValueError(f"Rental agreement {rental_agreement_id} not found")
        
        if rental.is_completed:
            raise ValueError(f"Cannot extend completed rental {rental_agreement_id}")
        
        # Check for conflicting reservations for the same vehicle
        if self._has_reservation_conflict(rental.vehicle.id, 
                                         rental.expected_return_time, 
                                         new_return_time):
            return False
        
        # Update return time and deposit if needed
        rental.expected_return_time = new_return_time
        rental.reservation.return_time = new_return_time
        
        # Log extension event
        self.audit_logger.log_event(
            timestamp=self.clock.now(),
            event_type=AuditEventType.RENTAL_EXTENSION,
            actor_type="System",
            actor_id=None,
            actor_name="System",
            entity_type="RentalAgreement",
            entity_id=rental.id,
            description=f"Rental extended to {new_return_time.isoformat()}",
            metadata={
                'rental_agreement_id': rental.id,
                'original_return_time': rental.expected_return_time.isoformat(),
                'new_return_time': new_return_time.isoformat()
            }
        )
        
        # Note: In a real system, you might need to adjust the deposit here
        # based on the additional days
        
        return True
    
    def _has_reservation_conflict(self, vehicle_id: int, start_time, end_time) -> bool:
        """
        Check if there's a reservation conflict for a vehicle in a time range.
        
        This is a simplified version. In a real system, you'd check against
        a reservation database or service.
        
        Args:
            vehicle_id: The vehicle ID to check
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            True if there's a conflict, False otherwise
        """
        # Simplified: check if vehicle is already rented during this period
        # In reality, you'd check against pending reservations
        return False
    
    def get_active_rental_by_vehicle(self, vehicle_id: int) -> Optional[RentalAgreement]:
        """
        Get the active rental for a vehicle.
        
        Args:
            vehicle_id: The vehicle ID
            
        Returns:
            The active rental agreement, or None if not rented
        """
        rental_id = self.vehicle_rentals.get(vehicle_id)
        if rental_id:
            return self.rental_agreements.get(rental_id)
        return None
    
    def get_rental_by_id(self, rental_id: int) -> Optional[RentalAgreement]:
        """
        Get a rental agreement by ID.
        
        Args:
            rental_id: The rental agreement ID
            
        Returns:
            The rental agreement, or None if not found
        """
        return self.rental_agreements.get(rental_id)
    
    def list_active_rentals(self) -> list[RentalAgreement]:
        """
        List all active (not completed) rentals.
        
        Returns:
            List of active rental agreements
        """
        return [r for r in self.rental_agreements.values() if not r.is_completed]
    
    def list_overdue_rentals(self, grace_period_hours: int = 1) -> list[RentalAgreement]:
        """
        List all overdue rentals.
        
        Args:
            grace_period_hours: Grace period in hours
            
        Returns:
            List of overdue rental agreements
        """
        current_time = self.clock.now()
        return [r for r in self.rental_agreements.values() 
                if not r.is_completed and r.is_overdue(current_time, grace_period_hours)]
    
    def add_manual_damage_charge(self, rental_agreement_id: int, damage_amount, 
                                 description: str, agent: Optional[Agent] = None) -> bool:
        """
        Add a manual damage charge to a rental agreement.
        
        Args:
            rental_agreement_id: The rental agreement ID
            damage_amount: The damage charge amount (Money)
            description: Description of the damage
            agent: The agent adding the charge
            
        Returns:
            True if successful, False if rental not found
        """
        from ..domain.models import ChargeItem
        
        rental = self.rental_agreements.get(rental_agreement_id)
        if not rental:
            return False
        
        charge_item = ChargeItem(
            description=f"Damage charge: {description}",
            amount=damage_amount
        )
        rental.add_charge(charge_item)
        
        # Log manual damage charge
        self.audit_logger.log_event(
            timestamp=self.clock.now(),
            event_type=AuditEventType.MANUAL_DAMAGE_CHARGE,
            actor_type="Agent" if agent else "System",
            actor_id=agent.id if agent else None,
            actor_name=agent.name if agent else "System",
            entity_type="RentalAgreement",
            entity_id=rental.id,
            description=f"Manual damage charge added: {description}",
            metadata={
                'rental_agreement_id': rental.id,
                'amount': str(damage_amount),
                'description': description
            }
        )
        
        return True