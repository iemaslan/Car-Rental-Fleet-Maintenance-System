"""
Test suite for maintenance logic and vehicle maintenance scheduling.
Tests verify maintenance-due detection based on odometer and time thresholds,
and that maintenance-due vehicles cannot be assigned to new rentals.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from domain.models import VehicleStatus, MaintenanceRecord
from domain.value_objects import Money, FuelLevel, Kilometers


class TestMaintenanceRegistration:
    """Test maintenance plan registration."""
    
    def test_register_odometer_based_maintenance(self, maintenance_service, 
                                                 economy_vehicle):
        """Test registering odometer-based maintenance plan."""
        record = maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(55000)
        )
        
        assert record is not None
        assert record.vehicle == economy_vehicle
        assert record.service_type == "Oil Change"
        assert record.odometer_threshold == Kilometers(55000)
        assert record.time_threshold is None
    
    def test_register_time_based_maintenance(self, maintenance_service, 
                                            economy_vehicle, fixed_clock):
        """Test registering time-based maintenance plan."""
        threshold_time = fixed_clock.now() + timedelta(days=90)
        
        record = maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Inspection",
            odometer_threshold=Kilometers(100000),  # High threshold
            time_threshold=threshold_time
        )
        
        assert record.time_threshold == threshold_time
    
    def test_register_multiple_maintenance_plans(self, maintenance_service, 
                                                economy_vehicle, fixed_clock):
        """Test registering multiple maintenance plans for same vehicle."""
        # Oil change
        record1 = maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(55000)
        )
        
        # Tire rotation
        record2 = maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Tire Rotation",
            odometer_threshold=Kilometers(60000)
        )
        
        assert record1.id != record2.id
        assert len(maintenance_service.maintenance_records[economy_vehicle.id]) == 2


class TestMaintenanceDueDetection:
    """Test maintenance-due detection logic."""
    
    def test_maintenance_due_odometer_threshold_reached(self, maintenance_service, 
                                                       economy_vehicle):
        """Test vehicle is flagged as maintenance-due when odometer threshold is reached."""
        # Current odometer: 50000
        # Register maintenance at 50500
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(50500)
        )
        
        # Should be due at boundary (exactly 500 km before threshold)
        # 50000 >= (50500 - 500) = 50000 >= 50000 = True
        assert maintenance_service.is_maintenance_due(economy_vehicle)
        
        # Update odometer to move closer to threshold
        economy_vehicle.odometer = Kilometers(50100)
        
        # Should still be due (now 400 km before threshold, still within 500 km warning)
        # 50100 >= (50500 - 500) = 50100 >= 50000 = True  
        assert maintenance_service.is_maintenance_due(economy_vehicle)
    
    def test_maintenance_due_odometer_exceeded(self, maintenance_service, 
                                              economy_vehicle):
        """Test vehicle is flagged when odometer has exceeded threshold."""
        # Current odometer: 50000
        # Register maintenance at 49000 (already passed)
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(49000)
        )
        
        # Should be due (threshold already passed)
        assert maintenance_service.is_maintenance_due(economy_vehicle)
    
    def test_maintenance_due_time_threshold_reached(self, maintenance_service, 
                                                   economy_vehicle, fixed_clock):
        """Test vehicle is flagged when time threshold is reached."""
        current_time = fixed_clock.now()
        threshold_time = current_time + timedelta(days=30)
        
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Inspection",
            odometer_threshold=Kilometers(100000),  # High threshold, won't trigger
            time_threshold=threshold_time
        )
        
        # Not due yet
        assert not maintenance_service.is_maintenance_due(economy_vehicle)
        
        # Advance time past threshold
        fixed_clock.set_time(threshold_time + timedelta(days=1))
        
        # Should be due now
        assert maintenance_service.is_maintenance_due(economy_vehicle)
    
    def test_maintenance_not_due_below_thresholds(self, maintenance_service, 
                                                  economy_vehicle, fixed_clock):
        """Test vehicle is not flagged when below all thresholds."""
        current_time = fixed_clock.now()
        
        # Register maintenance far in future
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(80000),
            time_threshold=current_time + timedelta(days=180)
        )
        
        # Should not be due
        assert not maintenance_service.is_maintenance_due(economy_vehicle)
    
    def test_maintenance_due_custom_threshold(self, maintenance_service, 
                                             economy_vehicle):
        """Test maintenance-due detection with custom km threshold."""
        # Current odometer: 50000
        # Register at 51000
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(51000)
        )
        
        # Not due with default 500 km threshold
        assert not maintenance_service.is_maintenance_due(economy_vehicle, threshold_km=500)
        
        # Due with larger 2000 km threshold
        assert maintenance_service.is_maintenance_due(economy_vehicle, threshold_km=2000)
    
    def test_maintenance_due_any_plan_triggers(self, maintenance_service, 
                                              economy_vehicle, fixed_clock):
        """Test vehicle is due if ANY maintenance plan triggers."""
        current_time = fixed_clock.now()
        
        # Register two plans: one due, one not
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(49000)  # Already passed - DUE
        )
        
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Tire Rotation",
            odometer_threshold=Kilometers(80000)  # Far in future - NOT DUE
        )
        
        # Should be due because oil change is due
        assert maintenance_service.is_maintenance_due(economy_vehicle)


class TestMaintenanceVehicleAssignment:
    """Test that maintenance-due vehicles cannot be assigned."""
    
    def test_cannot_assign_maintenance_due_vehicle(self, maintenance_service, 
                                                   economy_vehicle):
        """Test vehicle cannot be assigned when maintenance is due."""
        # Register overdue maintenance
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(49000)
        )
        
        # Vehicle should not be assignable
        assert not maintenance_service.can_vehicle_be_assigned(economy_vehicle)
    
    def test_can_assign_vehicle_no_maintenance_due(self, maintenance_service, 
                                                   economy_vehicle):
        """Test vehicle can be assigned when no maintenance is due."""
        # Register future maintenance
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(80000)
        )
        
        # Vehicle should be assignable
        assert maintenance_service.can_vehicle_be_assigned(economy_vehicle)
    
    def test_cannot_assign_vehicle_wrong_status(self, maintenance_service, 
                                               economy_vehicle):
        """Test vehicle cannot be assigned due to status even if no maintenance due."""
        # No maintenance registered, but vehicle out of service
        economy_vehicle.status = VehicleStatus.OUT_OF_SERVICE
        
        assert not maintenance_service.can_vehicle_be_assigned(economy_vehicle)
    
    def test_pickup_fails_maintenance_due(self, rental_service, basic_reservation, 
                                         economy_vehicle, maintenance_service, 
                                         fixed_clock):
        """Test pickup operation fails when vehicle is maintenance-due."""
        # Register overdue maintenance
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(49000)
        )
        
        fixed_clock.set_time(basic_reservation.pickup_time)
        
        with pytest.raises(ValueError, match="due for maintenance"):
            rental_service.pickup_vehicle(
                reservation=basic_reservation,
                vehicle=economy_vehicle,
                start_odometer=Kilometers(50000),
                start_fuel_level=FuelLevel(1.0)
            )


class TestMaintenanceCompletion:
    """Test maintenance completion functionality."""
    
    def test_complete_maintenance_updates_record(self, maintenance_service, 
                                                economy_vehicle, fixed_clock):
        """Test completing maintenance updates the record."""
        # Register maintenance
        record = maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(55000)
        )
        
        # Update vehicle for service
        current_time = fixed_clock.now()
        economy_vehicle.odometer = Kilometers(50500)
        
        # Complete maintenance
        maintenance_service.complete_maintenance(economy_vehicle, "Oil Change")
        
        # Record should be updated
        assert record.last_service_date == current_time
        assert record.last_service_odometer == Kilometers(50500)


class TestMaintenanceQueries:
    """Test maintenance query operations."""
    
    def test_list_due_vehicles(self, maintenance_service, economy_vehicle, 
                              suv_vehicle, luxury_vehicle):
        """Test listing all vehicles due for maintenance."""
        # Register maintenance for different vehicles
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(49000)  # DUE
        )
        
        maintenance_service.register_maintenance_plan(
            vehicle=suv_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(80000)  # NOT DUE (current: 30000)
        )
        
        maintenance_service.register_maintenance_plan(
            vehicle=luxury_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(14000)  # DUE (current: 15000)
        )
        
        due_vehicles = maintenance_service.list_due_vehicles(
            [economy_vehicle, suv_vehicle, luxury_vehicle]
        )
        
        assert len(due_vehicles) == 2
        assert economy_vehicle in due_vehicles
        assert luxury_vehicle in due_vehicles
        assert suv_vehicle not in due_vehicles
    
    def test_get_due_maintenance_records(self, maintenance_service, 
                                        economy_vehicle, fixed_clock):
        """Test getting specific due maintenance records for a vehicle."""
        current_time = fixed_clock.now()
        
        # Register multiple maintenance plans
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(49000)  # DUE
        )
        
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Tire Rotation",
            odometer_threshold=Kilometers(80000)  # NOT DUE
        )
        
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Inspection",
            odometer_threshold=Kilometers(100000),
            time_threshold=current_time - timedelta(days=1)  # DUE (time-based)
        )
        
        due_records = maintenance_service.get_due_maintenance_records(economy_vehicle)
        
        assert len(due_records) == 2
        service_types = [r.service_type for r in due_records]
        assert "Oil Change" in service_types
        assert "Inspection" in service_types
        assert "Tire Rotation" not in service_types


@pytest.mark.parametrize("current_odometer,threshold,threshold_km,expected_due", [
    (50000, 50500, 500, True),    # 500 km away, threshold 500 = at boundary, should be due
    (50000, 50499, 500, True),    # 499 km away, within threshold
    (50000, 49500, 500, True),    # Already passed
    (50000, 51000, 500, False),   # 1000 km away, not due
    (50000, 51000, 1500, True),   # 1000 km away, but threshold is 1500
    (50000, 50100, 500, True),    # 100 km away, due
    (50000, 50000, 500, True),    # Exactly at threshold
])
def test_odometer_threshold_scenarios(current_odometer, threshold, threshold_km, 
                                     expected_due, maintenance_service, 
                                     economy_vehicle):
    """Parametrized test for various odometer threshold scenarios."""
    economy_vehicle.odometer = Kilometers(current_odometer)
    
    maintenance_service.register_maintenance_plan(
        vehicle=economy_vehicle,
        service_type="Oil Change",
        odometer_threshold=Kilometers(threshold)
    )
    
    is_due = maintenance_service.is_maintenance_due(economy_vehicle, 
                                                    threshold_km=threshold_km)
    assert is_due == expected_due


@pytest.mark.parametrize("days_until_threshold,expected_due", [
    (30, False),   # 30 days in future
    (1, False),    # 1 day in future
    (0, True),     # Today
    (-1, True),    # 1 day overdue
    (-30, True),   # 30 days overdue
])
def test_time_threshold_scenarios(days_until_threshold, expected_due, 
                                 maintenance_service, economy_vehicle, 
                                 fixed_clock):
    """Parametrized test for various time threshold scenarios."""
    current_time = fixed_clock.now()
    threshold_time = current_time + timedelta(days=days_until_threshold)
    
    maintenance_service.register_maintenance_plan(
        vehicle=economy_vehicle,
        service_type="Inspection",
        odometer_threshold=Kilometers(100000),  # Won't trigger
        time_threshold=threshold_time
    )
    
    is_due = maintenance_service.is_maintenance_due(economy_vehicle)
    assert is_due == expected_due


class TestMaintenanceIntegration:
    """Test maintenance integration with rental workflow."""
    
    def test_vehicle_becomes_due_during_rental(self, rental_service, 
                                              maintenance_service, 
                                              basic_reservation, 
                                              economy_vehicle, fixed_clock):
        """Test vehicle that becomes maintenance-due during active rental."""
        # Register maintenance that will be due after some driving
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(50700)
        )
        
        # Pickup (odometer: 50000)
        fixed_clock.set_time(basic_reservation.pickup_time)
        rental = rental_service.pickup_vehicle(
            reservation=basic_reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0)
        )
        
        # Return after driving 800 km (odometer: 50800)
        fixed_clock.set_time(rental.expected_return_time)
        rental_service.return_vehicle(
            rental_agreement_id=rental.id,
            end_odometer=Kilometers(50800),
            end_fuel_level=FuelLevel(1.0)
        )
        
        # Vehicle should now be maintenance-due
        assert maintenance_service.is_maintenance_due(economy_vehicle)
        
        # Should not be assignable for next rental
        assert not maintenance_service.can_vehicle_be_assigned(economy_vehicle)
    
    def test_maintenance_completed_vehicle_assignable(self, maintenance_service, 
                                                     economy_vehicle, fixed_clock):
        """Test vehicle becomes assignable after maintenance completion."""
        # Register and trigger maintenance
        maintenance_service.register_maintenance_plan(
            vehicle=economy_vehicle,
            service_type="Oil Change",
            odometer_threshold=Kilometers(49000)
        )
        
        # Vehicle is due
        assert maintenance_service.is_maintenance_due(economy_vehicle)
        assert not maintenance_service.can_vehicle_be_assigned(economy_vehicle)
        
        # Complete maintenance and update threshold
        maintenance_service.complete_maintenance(economy_vehicle, "Oil Change")
        
        # Update to new threshold (would typically re-register)
        # For this test, manually update the record
        records = maintenance_service.maintenance_records[economy_vehicle.id]
        for record in records:
            if record.service_type == "Oil Change":
                record.odometer_threshold = Kilometers(55000)
        
        # Vehicle should now be assignable
        assert not maintenance_service.is_maintenance_due(economy_vehicle)
        assert maintenance_service.can_vehicle_be_assigned(economy_vehicle)
