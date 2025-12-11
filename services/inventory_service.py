"""
Inventory service for managing vehicle availability and searching.
"""
from typing import List, Dict, Tuple
from datetime import datetime
from domain.models import Vehicle, VehicleClass, Location, VehicleStatus
from domain.clock import Clock
from services.maintenance_service import MaintenanceService


class InventoryService:
    """Service for managing vehicle inventory and availability."""
    
    def __init__(self, clock: Clock, maintenance_service: MaintenanceService):
        self.clock = clock
        self.maintenance_service = maintenance_service
        self.vehicles: Dict[int, Vehicle] = {}

    def add_vehicle(self, vehicle: Vehicle) -> None:
        """
        Add a vehicle to the inventory.
        
        Args:
            vehicle: The vehicle to add
        """
        self.vehicles[vehicle.id] = vehicle

    def get_vehicle(self, vehicle_id: int) -> Vehicle:
        """
        Get a vehicle by ID.
        
        Args:
            vehicle_id: The vehicle ID
            
        Returns:
            The vehicle
            
        Raises:
            ValueError: If vehicle not found
        """
        vehicle = self.vehicles.get(vehicle_id)
        if not vehicle:
            raise ValueError(f"Vehicle {vehicle_id} not found")
        return vehicle

    def check_availability(self, vehicle_class: VehicleClass, location: Location, 
                          start_time: datetime, end_time: datetime) -> Dict[str, any]:
        """
        Check which vehicles of a given class are available at a location within a time range.
        Includes inventory counts and maintenance holds.
        
        Args:
            vehicle_class: The vehicle class to search for
            location: The location to search at
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Dictionary with availability information including:
            - available_count: Number of available vehicles
            - total_count: Total vehicles of this class at location
            - maintenance_hold_count: Number of vehicles in maintenance
            - available_vehicles: List of available vehicle IDs
        """
        # Find all vehicles of this class at this location
        matching_vehicles = [
            v for v in self.vehicles.values()
            if v.vehicle_class.name == vehicle_class.name and v.location.id == location.id
        ]
        
        total_count = len(matching_vehicles)
        
        # Count maintenance holds
        maintenance_holds = [
            v for v in matching_vehicles
            if self.maintenance_service.is_maintenance_due(v)
        ]
        maintenance_hold_count = len(maintenance_holds)
        
        # Find available vehicles (not rented, not in maintenance)
        available_vehicles = [
            v for v in matching_vehicles
            if v.status == VehicleStatus.AVAILABLE and 
               not self.maintenance_service.is_maintenance_due(v)
        ]
        
        available_count = len(available_vehicles)
        available_vehicle_ids = [v.id for v in available_vehicles]
        
        return {
            'vehicle_class': vehicle_class.name,
            'location': location.name,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'available_count': available_count,
            'total_count': total_count,
            'maintenance_hold_count': maintenance_hold_count,
            'available_vehicles': available_vehicle_ids,
        }
    
    def search_available_classes(self, location: Location, 
                                start_time: datetime, 
                                end_time: datetime) -> List[Dict[str, any]]:
        """
        Search for all available vehicle classes at a location for a time range.
        
        Args:
            location: The location to search at
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            List of availability information for each class
        """
        # Get all unique vehicle classes at this location
        vehicle_classes = set()
        for vehicle in self.vehicles.values():
            if vehicle.location.id == location.id:
                vehicle_classes.add(vehicle.vehicle_class)
        
        # Check availability for each class
        results = []
        for vehicle_class in vehicle_classes:
            availability = self.check_availability(
                vehicle_class, location, start_time, end_time
            )
            if availability['available_count'] > 0:
                results.append(availability)
        
        return results
    
    def list_vehicles_by_location(self, location: Location) -> List[Vehicle]:
        """
        List all vehicles at a location.
        
        Args:
            location: The location
            
        Returns:
            List of vehicles at the location
        """
        return [v for v in self.vehicles.values() if v.location.id == location.id]
    
    def list_vehicles_by_class(self, vehicle_class: VehicleClass) -> List[Vehicle]:
        """
        List all vehicles of a specific class.
        
        Args:
            vehicle_class: The vehicle class
            
        Returns:
            List of vehicles of that class
        """
        return [v for v in self.vehicles.values() 
                if v.vehicle_class.name == vehicle_class.name]
    
    def get_vehicle_statistics(self) -> Dict[str, any]:
        """
        Get overall vehicle statistics.
        
        Returns:
            Dictionary with statistics
        """
        total = len(self.vehicles)
        available = sum(1 for v in self.vehicles.values() 
                       if v.status == VehicleStatus.AVAILABLE)
        rented = sum(1 for v in self.vehicles.values() 
                    if v.status == VehicleStatus.RENTED)
        maintenance = sum(1 for v in self.vehicles.values() 
                         if v.status == VehicleStatus.OUT_OF_SERVICE)
        cleaning = sum(1 for v in self.vehicles.values() 
                      if v.status == VehicleStatus.CLEANING)
        
        # Count by class
        by_class = {}
        for v in self.vehicles.values():
            class_name = v.vehicle_class.name
            by_class[class_name] = by_class.get(class_name, 0) + 1
        
        # Count by location
        by_location = {}
        for v in self.vehicles.values():
            location_name = v.location.name
            by_location[location_name] = by_location.get(location_name, 0) + 1
        
        return {
            'total_count': total,
            'available_count': available,
            'rented_count': rented,
            'under_maintenance_count': maintenance,
            'cleaning_count': cleaning,
            'by_class': by_class,
            'by_location': by_location,
        }