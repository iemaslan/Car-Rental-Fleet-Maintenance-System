"""
Test suite for rental extension and reservation conflict logic.
Tests verify that rentals can be extended only when no overlapping
reservations exist for the same vehicle. Uses parametrized tests
for various conflict scenarios.
"""
import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from domain.models import Reservation, VehicleStatus
from domain.value_objects import Money, FuelLevel, Kilometers


class TestRentalExtension:
    """Test rental extension operations."""
    
    def test_extend_rental_success_no_conflict(self, rental_service, 
                                              basic_reservation, 
                                              economy_vehicle, fixed_clock):
        """Test successful rental extension when no conflicts exist."""
        # Pickup
        fixed_clock.set_time(basic_reservation.pickup_time)
        rental = rental_service.pickup_vehicle(
            reservation=basic_reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0)
        )
        
        # Try to extend by 2 days
        new_return_time = rental.expected_return_time + timedelta(days=2)
        result = rental_service.extend_rental(rental.id, new_return_time)
        
        assert result is True
        assert rental.expected_return_time == new_return_time
        assert rental.reservation.return_time == new_return_time
    
    def test_extend_rental_fails_completed_rental(self, completed_rental_scenario):
        """Test extension fails for already completed rental."""
        rental_service, rental, vehicle, fixed_clock = completed_rental_scenario
        
        new_return_time = rental.expected_return_time + timedelta(days=2)
        
        with pytest.raises(ValueError, match="Cannot extend completed rental"):
            rental_service.extend_rental(rental.id, new_return_time)
    
    def test_extend_rental_fails_nonexistent_rental(self, rental_service):
        """Test extension fails for non-existent rental."""
        new_return_time = datetime(2025, 12, 20, 10, 0, 0)
        
        with pytest.raises(ValueError, match="not found"):
            rental_service.extend_rental(999, new_return_time)
    
    def test_extend_rental_updates_audit_log(self, rental_service, 
                                            basic_reservation, 
                                            economy_vehicle, 
                                            fixed_clock, audit_logger):
        """Test extension logs audit event."""
        # Pickup
        fixed_clock.set_time(basic_reservation.pickup_time)
        rental = rental_service.pickup_vehicle(
            reservation=basic_reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0)
        )
        
        initial_event_count = len(audit_logger.entries)
        
        # Extend
        new_return_time = rental.expected_return_time + timedelta(days=2)
        rental_service.extend_rental(rental.id, new_return_time)
        
        # Should have added extension event
        assert len(audit_logger.entries) > initial_event_count
        
        # Find extension event
        from domain.audit_log import AuditEventType
        extension_events = [e for e in audit_logger.entries 
                          if e.event_type == AuditEventType.RENTAL_EXTENSION]
        assert len(extension_events) > 0


class TestReservationConflictDetection:
    """Test reservation conflict detection logic."""
    
    def test_no_conflict_different_vehicles(self, rental_service, customer, 
                                           economy_class, location, 
                                           economy_vehicle, suv_vehicle, 
                                           fixed_clock):
        """Test no conflict when reservations are for different vehicles."""
        # Create and activate rental on economy vehicle
        pickup1 = datetime(2025, 12, 10, 10, 0, 0)
        return1 = pickup1 + timedelta(days=3)
        
        reservation1 = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup1, return_time=return1,
            addons=[], insurance_tier=None
        )
        
        fixed_clock.set_time(pickup1)
        rental1 = rental_service.pickup_vehicle(
            reservation=reservation1,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0)
        )
        
        # Try to extend into period when SUV vehicle has reservation (should succeed)
        # Since they're different vehicles, there's no conflict
        new_return_time = return1 + timedelta(days=2)
        result = rental_service.extend_rental(rental1.id, new_return_time)
        
        # Should succeed (different vehicles)
        assert result is True


class TestConflictScenarios:
    """Test various conflict scenarios with helper method to add conflicts."""
    
    def setup_rental_with_conflict_detection(self, rental_service, customer, 
                                            economy_class, location, 
                                            economy_vehicle, fixed_clock):
        """
        Helper to set up a rental and add conflict detection capability.
        Returns rental service with enhanced conflict checking.
        """
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        fixed_clock.set_time(pickup)
        rental = rental_service.pickup_vehicle(
            reservation=reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0)
        )
        
        # Store pending reservations for conflict detection
        rental_service.pending_reservations = {}
        
        # Override conflict detection to use pending reservations
        original_check = rental_service._has_reservation_conflict
        
        def enhanced_conflict_check(vehicle_id, start_time, end_time):
            if vehicle_id not in rental_service.pending_reservations:
                return False
            
            for res in rental_service.pending_reservations[vehicle_id]:
                # Check for overlap
                if not (end_time <= res['start'] or start_time >= res['end']):
                    return True
            return False
        
        rental_service._has_reservation_conflict = enhanced_conflict_check
        
        return rental, rental_service
    
    def add_pending_reservation(self, rental_service, vehicle_id, start_time, end_time):
        """Add a pending reservation for conflict detection."""
        if vehicle_id not in rental_service.pending_reservations:
            rental_service.pending_reservations[vehicle_id] = []
        
        rental_service.pending_reservations[vehicle_id].append({
            'start': start_time,
            'end': end_time
        })
    
    def test_extension_blocked_by_overlapping_reservation(self, rental_service, 
                                                         customer, economy_class, 
                                                         location, economy_vehicle, 
                                                         fixed_clock):
        """Test extension fails when it would overlap with existing reservation."""
        rental, service = self.setup_rental_with_conflict_detection(
            rental_service, customer, economy_class, location, 
            economy_vehicle, fixed_clock
        )
        
        # Add pending reservation that would conflict
        # Current rental: Dec 10-13
        # Pending reservation: Dec 13-15
        # Try to extend to Dec 14 (would overlap)
        conflict_start = rental.expected_return_time
        conflict_end = conflict_start + timedelta(days=2)
        self.add_pending_reservation(service, economy_vehicle.id, 
                                    conflict_start, conflict_end)
        
        # Try to extend to Dec 14 (conflicts with Dec 13-15 reservation)
        new_return_time = rental.expected_return_time + timedelta(days=1)
        result = service.extend_rental(rental.id, new_return_time)
        
        assert result is False
        # Original return time should be unchanged
        assert rental.expected_return_time == datetime(2025, 12, 13, 10, 0, 0)
    
    def test_extension_allowed_no_overlap(self, rental_service, customer, 
                                         economy_class, location, 
                                         economy_vehicle, fixed_clock):
        """Test extension succeeds when no overlap with future reservations."""
        rental, service = self.setup_rental_with_conflict_detection(
            rental_service, customer, economy_class, location, 
            economy_vehicle, fixed_clock
        )
        
        # Add pending reservation that doesn't conflict
        # Current rental: Dec 10-13
        # Pending reservation: Dec 16-18
        # Try to extend to Dec 14 (no overlap)
        no_conflict_start = rental.expected_return_time + timedelta(days=3)
        no_conflict_end = no_conflict_start + timedelta(days=2)
        self.add_pending_reservation(service, economy_vehicle.id, 
                                    no_conflict_start, no_conflict_end)
        
        # Extend to Dec 14 (no conflict with Dec 16-18 reservation)
        new_return_time = rental.expected_return_time + timedelta(days=1)
        result = service.extend_rental(rental.id, new_return_time)
        
        assert result is True
        assert rental.expected_return_time == new_return_time


@pytest.mark.parametrize("extension_days,conflict_start_offset,conflict_duration,should_allow", [
    # (extension days, days until conflict starts, conflict duration, expected result)
    (1, 1, 2, True),    # Extend 1 day, conflict starts 1 day after - ends exactly at conflict start (boundary - allowed)
    (2, 3, 2, True),    # Extend 2 days, conflict starts 3 days after current end (no overlap)
    (1, 2, 2, True),    # Extend 1 day, conflict starts 2 days after current end
    (3, 1, 2, False),   # Extend 3 days, conflict starts 1 day after current end (overlaps into conflict)
    (5, 7, 2, True),    # Extend 5 days, conflict starts 7 days after current end
    (2, 0, 3, False),   # Extend 2 days, conflict starts at current end time (overlap)
])
def test_extension_conflict_scenarios(extension_days, conflict_start_offset, 
                                     conflict_duration, should_allow,
                                     rental_service, customer, economy_class, 
                                     location, economy_vehicle, fixed_clock):
    """
    Parametrized test for various extension and conflict scenarios.
    Tests different combinations of extension periods and conflicting reservations.
    """
    # Setup rental
    pickup = datetime(2025, 12, 10, 10, 0, 0)
    current_return = pickup + timedelta(days=3)
    
    reservation = Reservation(
        id=1, customer=customer, vehicle_class=economy_class,
        location=location, pickup_time=pickup, return_time=current_return,
        addons=[], insurance_tier=None
    )
    
    fixed_clock.set_time(pickup)
    rental = rental_service.pickup_vehicle(
        reservation=reservation,
        vehicle=economy_vehicle,
        start_odometer=Kilometers(50000),
        start_fuel_level=FuelLevel(1.0)
    )
    
    # Setup conflict detection
    rental_service.pending_reservations = {}
    
    def enhanced_conflict_check(vehicle_id, start_time, end_time):
        if vehicle_id not in rental_service.pending_reservations:
            return False
        
        for res in rental_service.pending_reservations[vehicle_id]:
            if not (end_time <= res['start'] or start_time >= res['end']):
                return True
        return False
    
    rental_service._has_reservation_conflict = enhanced_conflict_check
    
    # Add pending reservation
    conflict_start = current_return + timedelta(days=conflict_start_offset)
    conflict_end = conflict_start + timedelta(days=conflict_duration)
    
    if economy_vehicle.id not in rental_service.pending_reservations:
        rental_service.pending_reservations[economy_vehicle.id] = []
    
    rental_service.pending_reservations[economy_vehicle.id].append({
        'start': conflict_start,
        'end': conflict_end
    })
    
    # Attempt extension
    new_return_time = current_return + timedelta(days=extension_days)
    result = rental_service.extend_rental(rental.id, new_return_time)
    
    assert result == should_allow
    
    if should_allow:
        assert rental.expected_return_time == new_return_time
    else:
        assert rental.expected_return_time == current_return


@pytest.mark.parametrize("scenario_name,current_start,current_end,new_end,conflict_start,conflict_end,expected", [
    # No conflict scenarios
    ("extend_before_conflict", "2025-12-10 10:00", "2025-12-13 10:00", 
     "2025-12-14 10:00", "2025-12-16 10:00", "2025-12-18 10:00", True),
    
    ("extend_ends_at_conflict_start", "2025-12-10 10:00", "2025-12-13 10:00",
     "2025-12-15 10:00", "2025-12-15 10:00", "2025-12-17 10:00", True),  # boundary - allowed
    
    # Conflict scenarios
    ("extend_into_conflict", "2025-12-10 10:00", "2025-12-13 10:00",
     "2025-12-16 10:00", "2025-12-14 10:00", "2025-12-17 10:00", False),
    
    ("extend_covers_conflict", "2025-12-10 10:00", "2025-12-13 10:00",
     "2025-12-20 10:00", "2025-12-14 10:00", "2025-12-16 10:00", False),
    
    ("small_extension_no_conflict", "2025-12-10 10:00", "2025-12-13 10:00",
     "2025-12-13 15:00", "2025-12-14 10:00", "2025-12-16 10:00", True),
])
def test_extension_time_scenarios(scenario_name, current_start, current_end, 
                                 new_end, conflict_start, conflict_end, expected,
                                 rental_service, customer, economy_class, 
                                 location, economy_vehicle, fixed_clock):
    """
    Parametrized test with explicit datetime scenarios for extension conflicts.
    Tests precise time boundaries and overlap conditions.
    """
    # Parse datetimes
    def parse_dt(dt_str):
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
    
    pickup = parse_dt(current_start)
    return_time = parse_dt(current_end)
    new_return = parse_dt(new_end)
    conf_start = parse_dt(conflict_start)
    conf_end = parse_dt(conflict_end)
    
    # Create reservation and rental
    reservation = Reservation(
        id=1, customer=customer, vehicle_class=economy_class,
        location=location, pickup_time=pickup, return_time=return_time,
        addons=[], insurance_tier=None
    )
    
    fixed_clock.set_time(pickup)
    rental = rental_service.pickup_vehicle(
        reservation=reservation,
        vehicle=economy_vehicle,
        start_odometer=Kilometers(50000),
        start_fuel_level=FuelLevel(1.0)
    )
    
    # Setup conflict detection
    rental_service.pending_reservations = {
        economy_vehicle.id: [{
            'start': conf_start,
            'end': conf_end
        }]
    }
    
    def enhanced_conflict_check(vehicle_id, start_time, end_time):
        if vehicle_id not in rental_service.pending_reservations:
            return False
        
        for res in rental_service.pending_reservations[vehicle_id]:
            if not (end_time <= res['start'] or start_time >= res['end']):
                return True
        return False
    
    rental_service._has_reservation_conflict = enhanced_conflict_check
    
    # Attempt extension
    result = rental_service.extend_rental(rental.id, new_return)
    
    assert result == expected, f"Scenario '{scenario_name}' failed"


class TestMultipleConflicts:
    """Test scenarios with multiple conflicting reservations."""
    
    def test_extension_with_multiple_conflicts(self, rental_service, customer, 
                                              economy_class, location, 
                                              economy_vehicle, fixed_clock):
        """Test extension fails when multiple future reservations would conflict."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        fixed_clock.set_time(pickup)
        rental = rental_service.pickup_vehicle(
            reservation=reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0)
        )
        
        # Add multiple pending reservations
        rental_service.pending_reservations = {
            economy_vehicle.id: [
                {'start': datetime(2025, 12, 14, 10, 0), 'end': datetime(2025, 12, 16, 10, 0)},
                {'start': datetime(2025, 12, 17, 10, 0), 'end': datetime(2025, 12, 19, 10, 0)},
                {'start': datetime(2025, 12, 20, 10, 0), 'end': datetime(2025, 12, 22, 10, 0)},
            ]
        }
        
        def enhanced_conflict_check(vehicle_id, start_time, end_time):
            if vehicle_id not in rental_service.pending_reservations:
                return False
            
            for res in rental_service.pending_reservations[vehicle_id]:
                if not (end_time <= res['start'] or start_time >= res['end']):
                    return True
            return False
        
        rental_service._has_reservation_conflict = enhanced_conflict_check
        
        # Try to extend to Dec 15 (conflicts with first reservation)
        new_return = datetime(2025, 12, 15, 10, 0, 0)
        result = rental_service.extend_rental(rental.id, new_return)
        assert result is False
        
        # Try to extend to Dec 13 (no conflict)
        new_return = datetime(2025, 12, 13, 18, 0, 0)
        result = rental_service.extend_rental(rental.id, new_return)
        assert result is True
    
    def test_extension_fits_between_reservations(self, rental_service, customer, 
                                                economy_class, location, 
                                                economy_vehicle, fixed_clock):
        """Test extension succeeds when it fits in gap between reservations."""
        pickup = datetime(2025, 12, 10, 10, 0, 0)
        return_time = pickup + timedelta(days=3)
        
        reservation = Reservation(
            id=1, customer=customer, vehicle_class=economy_class,
            location=location, pickup_time=pickup, return_time=return_time,
            addons=[], insurance_tier=None
        )
        
        fixed_clock.set_time(pickup)
        rental = rental_service.pickup_vehicle(
            reservation=reservation,
            vehicle=economy_vehicle,
            start_odometer=Kilometers(50000),
            start_fuel_level=FuelLevel(1.0)
        )
        
        # Add reservations with gap
        # Current: Dec 10-13
        # Gap: Dec 13-16
        # Reservation: Dec 16-18
        rental_service.pending_reservations = {
            economy_vehicle.id: [
                {'start': datetime(2025, 12, 16, 10, 0), 'end': datetime(2025, 12, 18, 10, 0)},
            ]
        }
        
        def enhanced_conflict_check(vehicle_id, start_time, end_time):
            if vehicle_id not in rental_service.pending_reservations:
                return False
            
            for res in rental_service.pending_reservations[vehicle_id]:
                if not (end_time <= res['start'] or start_time >= res['end']):
                    return True
            return False
        
        rental_service._has_reservation_conflict = enhanced_conflict_check
        
        # Extend to Dec 15 (fits in gap before Dec 16 reservation)
        new_return = datetime(2025, 12, 15, 10, 0, 0)
        result = rental_service.extend_rental(rental.id, new_return)
        assert result is True
        assert rental.expected_return_time == new_return
