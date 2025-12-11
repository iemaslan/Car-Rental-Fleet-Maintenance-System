"""
Audit log system for tracking all important operations and decisions.
Provides auditability for manual overrides, upgrades, and damage charges.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum


class AuditEventType(Enum):
    """Types of auditable events."""
    VEHICLE_PICKUP = "VehiclePickup"
    VEHICLE_RETURN = "VehicleReturn"
    VEHICLE_UPGRADE = "VehicleUpgrade"
    RENTAL_EXTENSION = "RentalExtension"
    MANUAL_DAMAGE_CHARGE = "ManualDamageCharge"
    MANUAL_ADJUSTMENT = "ManualAdjustment"
    MAINTENANCE_OVERRIDE = "MaintenanceOverride"
    PAYMENT_AUTHORIZATION = "PaymentAuthorization"
    PAYMENT_CAPTURE = "PaymentCapture"
    PAYMENT_FAILURE = "PaymentFailure"
    RESERVATION_CREATED = "ReservationCreated"
    RESERVATION_MODIFIED = "ReservationModified"
    RESERVATION_CANCELLED = "ReservationCancelled"


@dataclass
class AuditEntry:
    """Represents a single audit log entry."""
    id: int
    timestamp: datetime
    event_type: AuditEventType
    actor_type: str  # "Agent", "System", "Customer"
    actor_id: Optional[int]
    actor_name: Optional[str]
    entity_type: str  # "RentalAgreement", "Reservation", "Vehicle", etc.
    entity_id: int
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert audit entry to dictionary for serialization."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type.value,
            'actor_type': self.actor_type,
            'actor_id': self.actor_id,
            'actor_name': self.actor_name,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'description': self.description,
            'metadata': self.metadata
        }


class AuditLogger:
    """Service for logging auditable events."""
    
    def __init__(self):
        self.entries: List[AuditEntry] = []
        self.next_id = 1
    
    def log_event(self, timestamp: datetime, event_type: AuditEventType,
                 actor_type: str, actor_id: Optional[int], actor_name: Optional[str],
                 entity_type: str, entity_id: int, description: str,
                 metadata: Dict[str, Any] = None) -> AuditEntry:
        """
        Log an auditable event.
        
        Args:
            timestamp: When the event occurred
            event_type: Type of event
            actor_type: Type of actor (Agent, System, Customer)
            actor_id: ID of the actor
            actor_name: Name of the actor
            entity_type: Type of entity affected
            entity_id: ID of the entity
            description: Human-readable description
            metadata: Additional event-specific data
            
        Returns:
            The created audit entry
        """
        if metadata is None:
            metadata = {}
        
        entry = AuditEntry(
            id=self.next_id,
            timestamp=timestamp,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            actor_name=actor_name,
            entity_type=entity_type,
            entity_id=entity_id,
            description=description,
            metadata=metadata
        )
        
        self.next_id += 1
        self.entries.append(entry)
        return entry
    
    def get_entries_by_entity(self, entity_type: str, entity_id: int) -> List[AuditEntry]:
        """Get all audit entries for a specific entity."""
        return [e for e in self.entries 
                if e.entity_type == entity_type and e.entity_id == entity_id]
    
    def get_entries_by_event_type(self, event_type: AuditEventType) -> List[AuditEntry]:
        """Get all audit entries of a specific type."""
        return [e for e in self.entries if e.event_type == event_type]
    
    def get_entries_by_actor(self, actor_type: str, actor_id: int) -> List[AuditEntry]:
        """Get all audit entries by a specific actor."""
        return [e for e in self.entries 
                if e.actor_type == actor_type and e.actor_id == actor_id]
    
    def get_entries_in_timerange(self, start: datetime, end: datetime) -> List[AuditEntry]:
        """Get all audit entries within a time range."""
        return [e for e in self.entries if start <= e.timestamp <= end]
    
    def list_all_entries(self) -> List[AuditEntry]:
        """Get all audit entries."""
        return self.entries.copy()
    
    def export_to_dict(self) -> List[Dict[str, Any]]:
        """Export all audit entries as a list of dictionaries."""
        return [entry.to_dict() for entry in self.entries]
