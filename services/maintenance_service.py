"""
Maintenance service for managing vehicle maintenance plans and tracking due vehicles.
"""
from typing import List, Dict
from domain.models import MaintenanceRecord, Vehicle
from domain.value_objects import Kilometers
from domain.clock import Clock


class MaintenanceService:
    """Service for managing vehicle maintenance schedules."""
    
    def __init__(self, clock: Clock):
        self.clock = clock
        self.maintenance_records: Dict[int, List[MaintenanceRecord]] = {}  # vehicle_id -> records
        self.next_record_id = 1

    def register_maintenance_plan(self, vehicle: Vehicle, service_type: str, 
                                 odometer_threshold: Kilometers, 
                                 time_threshold=None) -> MaintenanceRecord:
        """
        Register a maintenance plan for a vehicle.
        
        Args:
            vehicle: The vehicle to register maintenance for
            service_type: Type of service (e.g., "Oil Change", "Tire Rotation")
            odometer_threshold: Odometer reading when maintenance is due
            time_threshold: Optional datetime when maintenance is due
            
        Returns:
            The created maintenance record
        """
        record = MaintenanceRecord(
            id=self.next_record_id,
            vehicle=vehicle,
            service_type=service_type,
            odometer_threshold=odometer_threshold,
            time_threshold=time_threshold
        )
        self.next_record_id += 1
        
        if vehicle.id not in self.maintenance_records:
            self.maintenance_records[vehicle.id] = []
        self.maintenance_records[vehicle.id].append(record)
        
        return record

    def is_maintenance_due(self, vehicle: Vehicle, threshold_km: int = 500) -> bool:
        """
        Check if any maintenance is due for a vehicle.
        
        Args:
            vehicle: The vehicle to check
            threshold_km: How many km before threshold to consider due (default 500)
            
        Returns:
            True if maintenance is due, False otherwise
        """
        if vehicle.id not in self.maintenance_records:
            return False
        
        current_time = self.clock.now()
        current_odometer = vehicle.odometer
        
        for record in self.maintenance_records[vehicle.id]:
            if record.is_due(current_odometer, current_time, threshold_km):
                return True
        
        return False

    def list_due_vehicles(self, vehicles: List[Vehicle], threshold_km: int = 500) -> List[Vehicle]:
        """
        List all vehicles that are due for maintenance.
        
        Args:
            vehicles: List of vehicles to check
            threshold_km: How many km before threshold to consider due (default 500)
            
        Returns:
            List of vehicles that are due for maintenance
        """
        due_vehicles = []
        
        for vehicle in vehicles:
            if self.is_maintenance_due(vehicle, threshold_km):
                due_vehicles.append(vehicle)
        
        return due_vehicles
    
    def get_due_maintenance_records(self, vehicle: Vehicle, threshold_km: int = 500) -> List[MaintenanceRecord]:
        """
        Get all due maintenance records for a vehicle.
        
        Args:
            vehicle: The vehicle to check
            threshold_km: How many km before threshold to consider due
            
        Returns:
            List of due maintenance records
        """
        if vehicle.id not in self.maintenance_records:
            return []
        
        current_time = self.clock.now()
        current_odometer = vehicle.odometer
        
        due_records = []
        for record in self.maintenance_records[vehicle.id]:
            if record.is_due(current_odometer, current_time, threshold_km):
                due_records.append(record)
        
        return due_records
    
    def can_vehicle_be_assigned(self, vehicle: Vehicle) -> bool:
        """
        Check if a vehicle can be assigned for rental.
        Considers both vehicle status and maintenance status.
        
        Args:
            vehicle: The vehicle to check
            
        Returns:
            True if vehicle can be assigned, False otherwise
        """
        # Check vehicle status
        if not vehicle.can_be_assigned():
            return False
        
        # Check maintenance status
        if self.is_maintenance_due(vehicle):
            return False
        
        return True
    
    def complete_maintenance(self, vehicle: Vehicle, service_type: str) -> None:
        """
        Mark maintenance as completed for a vehicle.
        Updates the maintenance record with current time and odometer.
        
        Args:
            vehicle: The vehicle that received maintenance
            service_type: The type of service completed
        """
        if vehicle.id not in self.maintenance_records:
            return
        
        current_time = self.clock.now()
        current_odometer = vehicle.odometer
        
        for record in self.maintenance_records[vehicle.id]:
            if record.service_type == service_type:
                record.last_service_date = current_time
                record.last_service_odometer = current_odometer
                # Reset thresholds for next maintenance
                # This is a simplified version - in reality, you'd add new thresholds
                break