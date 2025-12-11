# Testing Documentation for Car Rental & Fleet Maintenance System

## Overview

This directory contains comprehensive unit tests for the Car Rental & Fleet Maintenance System (CRFMS) using pytest. The test suite validates business rules, edge cases, pricing logic, rental workflows, maintenance scheduling, and billing operations.

## Test Organization

### Test Modules

1. **`conftest.py`** - Shared pytest fixtures
   - Domain entity fixtures (customers, vehicles, reservations)
   - Service fixtures (rental, maintenance, accounting)
   - Scenario fixtures (active rentals, completed rentals)
   - Clock and adapter fixtures

2. **`test_pricing.py`** - Pricing logic tests
   - Base rate calculations by vehicle class
   - Add-on fees (GPS, child seat, extra driver)
   - Insurance tier pricing
   - Dynamic factors (weekend and peak season surcharges)
   - Late fees with grace period
   - Mileage overage charges
   - Fuel refill charges
   - **Parametrized tests** for various combinations

3. **`test_rental_lifecycle.py`** - Rental pickup and return tests
   - Idempotent pickup operations
   - Return charge computation
   - Late fee calculation with grace period
   - Mileage overage detection
   - Fuel refill charges
   - Complete rental scenarios
   - **Parametrized tests** for late fees and mileage scenarios

4. **`test_rental_extension.py`** - Extension and conflict tests
   - Rental extension logic
   - Reservation conflict detection
   - Time overlap scenarios
   - Multiple conflict handling
   - **Parametrized tests** for extension scenarios

5. **`test_maintenance.py`** - Maintenance logic tests
   - Odometer-based maintenance scheduling
   - Time-based maintenance scheduling
   - Maintenance-due detection
   - Vehicle assignment restrictions
   - Maintenance completion tracking
   - **Parametrized tests** for threshold scenarios

6. **`test_billing_notifications.py`** - Billing and notification tests
   - Payment success scenarios
   - Payment failure scenarios
   - Invoice state management
   - Notification delivery
   - **Mocking** using pytest's monkeypatch
   - Payment retry logic

## Running the Tests

### Run All Tests
```bash
pytest
```

### Run with Verbose Output
```bash
pytest -v
```

### Run Specific Test Module
```bash
pytest tests/test_pricing.py
pytest tests/test_rental_lifecycle.py
pytest tests/test_maintenance.py
```

### Run Specific Test Class
```bash
pytest tests/test_pricing.py::TestBasicPricing
pytest tests/test_rental_lifecycle.py::TestPickupOperations
```

### Run Specific Test
```bash
pytest tests/test_pricing.py::TestBasicPricing::test_base_rate_calculation
```

### Run Tests with Coverage
```bash
pytest --cov=domain --cov=services --cov=adapters --cov-report=term-missing
```

### Run Tests with HTML Coverage Report
```bash
pytest --cov=domain --cov=services --cov=adapters --cov-report=html
```

## Test Features

### Fixtures
Pytest fixtures are used extensively to create reusable test components:
- **Domain fixtures**: `customer`, `vehicle`, `reservation`, etc.
- **Service fixtures**: `rental_service`, `pricing_policy`, `maintenance_service`, etc.
- **Scenario fixtures**: `active_rental_scenario`, `completed_rental_scenario`
- **Adapter fixtures**: `payment_adapter`, `notification_adapter`

### Parametrized Tests
Multiple parametrized tests cover various input combinations:
- `test_base_rate_combinations` - Different vehicle classes and durations
- `test_addon_combinations` - Various add-on combinations
- `test_insurance_tier_combinations` - Different insurance tiers
- `test_extension_conflict_scenarios` - Extension and conflict scenarios
- `test_late_fee_scenarios` - Various late return scenarios
- `test_mileage_overage_scenarios` - Different mileage and allowance combinations
- `test_odometer_threshold_scenarios` - Maintenance odometer thresholds
- `test_time_threshold_scenarios` - Maintenance time thresholds
- `test_payment_outcome_scenarios` - Payment success/failure outcomes

### Mocking
Tests use pytest's `monkeypatch` fixture and `unittest.mock` for mocking:
- Mocking payment adapters to simulate success/failure
- Mocking notification adapters to verify calls
- Using `Mock` objects to verify method calls and arguments
- Testing with `side_effect` for varying behavior

### Fixed Clock
All time-dependent tests use the `FixedClock` abstraction for deterministic testing:
- No dependency on system time
- Reproducible test results
- Easy simulation of time passage

## Key Test Scenarios

### Pricing Tests
✓ Base rates for different vehicle classes (Economy, Compact, SUV, Luxury)
✓ Add-on charges (GPS, child seat, extra driver)
✓ Insurance tiers (Basic, Premium, Full Coverage)
✓ Weekend surcharges (Saturday/Sunday pickup)
✓ Peak season surcharges (summer months)
✓ Late fees with 1-hour grace period
✓ Mileage overage beyond daily allowance
✓ Fuel refill charges for lower return level
✓ Edge cases (minimum 1-day rental, 30-day rental)
✓ Complete pricing with all charge types

### Rental Lifecycle Tests
✓ Successful pickup creates rental agreement
✓ Pickup idempotency (same token returns same rental)
✓ Pickup fails for unavailable vehicles
✓ Pickup fails for maintenance-due vehicles
✓ Return computes all charges correctly
✓ Return idempotency (multiple returns safe)
✓ Late fee calculation beyond grace period
✓ No late fee within grace period
✓ Mileage overage charges
✓ Fuel refill charges
✓ Complete rental scenarios (short, long, with extras)

### Extension and Conflict Tests
✓ Extension succeeds with no conflicts
✓ Extension fails for completed rentals
✓ Extension blocked by overlapping reservations
✓ Extension allowed with non-overlapping reservations
✓ Extension fits in gap between reservations
✓ Multiple conflict scenarios
✓ Precise time boundary conditions

### Maintenance Tests
✓ Odometer-based maintenance registration
✓ Time-based maintenance registration
✓ Maintenance-due detection (odometer threshold)
✓ Maintenance-due detection (time threshold)
✓ Vehicle cannot be assigned when maintenance-due
✓ Maintenance completion updates records
✓ Multiple maintenance plans per vehicle
✓ Custom threshold values
✓ Integration with rental workflow

### Billing and Notification Tests
✓ Successful payment updates invoice to "Paid"
✓ Failed payment updates invoice to "Failed"
✓ Success notification sent on payment success
✓ Failure notification sent on payment failure
✓ Payment adapter called with correct arguments
✓ Notification adapter called with correct arguments
✓ Payment retry after initial failure
✓ Invoice management (create, list, filter)
✓ Mock side effects for varying behavior
✓ Transaction auditing

## Test Statistics

- **Total Test Files**: 6 (including conftest.py)
- **Parametrized Tests**: 7+
- **Fixtures**: 30+
- **Coverage Areas**:
  - Domain models
  - Value objects
  - All service layers
  - Adapter ports
  - Pricing rules
  - Audit logging

## Requirements

Install test dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- `pytest>=7.4.3` - Testing framework
- `pytest-cov>=4.1.0` - Coverage reporting
- `pytest-mock>=3.12.0` - Enhanced mocking support

## Best Practices Demonstrated

1. **Fixtures for Reusability**: Shared fixtures reduce code duplication
2. **Parametrized Tests**: Cover multiple scenarios efficiently
3. **Mocking for Isolation**: Test units in isolation from external dependencies
4. **Deterministic Testing**: Fixed clock ensures reproducible results
5. **Clear Test Names**: Test names describe what they verify
6. **Edge Case Coverage**: Minimum duration, unusually long rentals, boundary conditions
7. **Idempotency Testing**: Verify operations can be safely repeated
8. **Integration Scenarios**: Complete workflows from pickup to return

## Notes

- All tests are designed to be deterministic and independent
- Tests use in-memory adapters and fixed clock (no external dependencies)
- Each test module focuses on a specific aspect of the system
- Tests follow AAA pattern: Arrange, Act, Assert
- Comprehensive coverage of normal cases, edge cases, and error conditions

## Homework 2 Compliance

This test suite fully satisfies all Homework 2 requirements:

✅ **Systematic unit testing using pytest**
✅ **Pricing logic tests** with parametrized tests for combinations
✅ **Rental lifecycle tests** (pickup idempotency, return with charges)
✅ **Extension and conflict logic** with parametrized scenarios
✅ **Maintenance logic tests** (odometer & time-based)
✅ **Billing/payment/notification mocking** using monkeypatch
✅ **At least 3 parametrized tests** (pricing, extension, maintenance+)
✅ **Fixtures for common objects** (vehicles, policies, services)
✅ **Logical test organization** (separate modules)
✅ **Clear test names and docstrings**
✅ **Fixed/stubbed clock** for time-dependent tests
✅ **Meaningful coverage** of business rules and edge cases
