# Car Rental & Fleet Maintenance System (CRFMS)

## Project Overview

A comprehensive car rental and fleet maintenance system implementing SOLID principles, using the Strategy pattern for pricing, and providing full auditability for all operations.

## Architecture & Design

### SOLID Principles Applied

1. **Single Responsibility Principle (SRP)**
   - Each service handles one aspect: `InventoryService`, `MaintenanceService`, `RentalService`, etc.
   - Value objects are immutable and handle only their domain logic
   - Ports separate interface from implementation

2. **Open/Closed Principle (OCP)**
   - Pricing rules can be added without modifying `PricingPolicy`
   - New add-ons can be added without changing core entities
   - Extensible through composition, not inheritance

3. **Liskov Substitution Principle (LSP)**
   - Clock implementations (`SystemClock`, `FixedClock`) are interchangeable
   - Payment and notification adapters follow their port contracts
   - All pricing rules implement the same interface

4. **Interface Segregation Principle (ISP)**
   - Small, focused ports: `PaymentPort`, `NotificationPort`
   - Each port defines only the operations needed by its clients
   
5. **Dependency Inversion Principle (DIP)**
   - Services depend on abstractions (ports) not concrete implementations
   - Clock injection allows testing with fixed time
   - Payment and notification systems are pluggable

### Design Patterns

#### Strategy Pattern
`PricingPolicy` composes multiple pricing rules that can be mixed and matched:
- `BaseRateRule`: Daily vehicle class rate
- `AddOnRule`: Per-day add-on fees
- `InsuranceRule`: Insurance tier fees
- `LateFeeRule`: Late return penalties with grace period
- `MileageOverageRule`: Overage beyond daily allowance
- `FuelRefillRule`: Fuel replacement charges
- `WeekendMultiplierRule`: Weekend surcharges
- `SeasonMultiplierRule`: Peak season multipliers
- `DamageChargeRule`: Manual damage charges

#### Ports and Adapters (Hexagonal Architecture)
- **Ports**: Abstract interfaces (`NotificationPort`, `PaymentPort`)
- **Adapters**: Concrete implementations
  - `InMemoryNotificationAdapter`: Test implementation
  - `FakePaymentAdapter`: Simulates payment processing

## Core Features

### 1. Value Objects (Immutable)
```python
Money(Decimal('50.00'), 'USD')     # Currency arithmetic
FuelLevel(0.8)                      # 0.0 to 1.0 scale
Kilometers(15000)                   # Non-negative distances
```

### 2. Injectable Clock
```python
SystemClock()                       # Production: uses system time
FixedClock(datetime(2025, 11, 4))  # Testing: deterministic time
```

### 3. Vehicle Management
- **States**: Available, Reserved, Rented, OutOfService, Cleaning
- **Maintenance tracking**: 500km threshold before service due
- **Automatic blocking**: Vehicles due for maintenance cannot be assigned

### 4. Idempotent Operations
```python
rental = rental_service.pickup_vehicle(
    reservation=reservation,
    vehicle=vehicle,
    pickup_token="unique-token-123"  # Ensures idempotency
)
```
Duplicate pickups with the same token return the existing rental.

### 5. Charge Computation
Automatic calculation of:
- Base rate (per day, per vehicle class)
- Add-on fees (GPS, ChildSeat, ExtraDriver, etc.)
- Insurance tier fees
- Late fees (1-hour grace period, then hourly charges)
- Mileage overage (based on daily allowance)
- Fuel refill charges (per 10% of tank)
- Manual damage charges

### 6. Reservation Management
- Create, modify, cancel reservations
- Automatic notifications (confirmation, modification, reminders)
- Support for add-ons and insurance tiers
- Deposit management

### 7. Rental Extensions
- Only allowed when no conflicting reservations exist
- Updates expected return time
- Adjusts charges accordingly

### 8. Audit Logging
Complete audit trail for:
- Vehicle pickups and returns
- Vehicle upgrades
- Rental extensions
- Manual damage charges
- Payment authorizations and captures
- Reservation lifecycle

### 9. Inventory Queries
```python
availability = inventory_service.check_availability(
    vehicle_class=economy_class,
    location=downtown_branch,
    start_time=pickup_date,
    end_time=return_date
)
# Returns: available_count, total_count, maintenance_hold_count, available_vehicles
```

### 10. Payment Processing
- Pre-authorization of deposits at pickup
- Final payment capture at return
- Failure handling with pending invoices
- Audit trail for all transactions

### 11. Notification System
Sends notifications for:
- Reservation confirmation
- Reservation modification
- Pickup reminders
- Overdue returns
- Invoice success/failure

## Module Structure

```
CRFMS/
├── domain/
│   ├── models.py           # Core entities
│   ├── value_objects.py    # Money, FuelLevel, Kilometers
│   ├── clock.py            # Clock interface and implementations
│   └── audit_log.py        # Audit logging system
├── services/
│   ├── inventory_service.py      # Vehicle availability
│   ├── maintenance_service.py    # Maintenance scheduling
│   ├── pricing_policy.py         # Pricing rules (Strategy pattern)
│   ├── rental_service.py         # Pickup, return, extension
│   ├── reservation_service.py    # Reservation management
│   └── accounting_service.py     # Invoicing and payments
├── adapters/
│   ├── notification_port.py      # Notification interface + adapter
│   └── payment_port.py           # Payment interface + adapter
└── tests/
    ├── test_comprehensive.py     # Full integration tests
    ├── test_rental_service.py
    ├── test_pricing_policy.py
    └── ...

demo.py                     # Comprehensive demonstration
```

## Running the Demo

```bash
cd /path/to/CRFMS
python3 demo.py
```

The demo script demonstrates:
- System setup with all services
- Creating test data (vehicles, customers, agents)
- Maintenance plan registration
- Inventory availability queries
- Creating reservations with notifications
- Idempotent vehicle pickup
- Rental extension
- Vehicle return with late fees
- Charge computation with all rules
- Manual damage charges
- Invoice and payment processing
- Complete audit trail

## Running Tests

```bash
cd CRFMS
python3 -m pytest tests/ -v
```

All tests use `FixedClock` for deterministic behavior.

## UML Class Diagram

See `docs/uml_class_diagram.puml` for the complete PlantUML diagram showing:
- All classes with attributes and methods
- Relationships with multiplicities
- Value objects, interfaces, and implementations
- Service dependencies

## Key Business Rules

### Maintenance
- Vehicles become maintenance-due within 500km of threshold
- Maintenance-due vehicles cannot be assigned to rentals
- Vehicles can have multiple maintenance plans

### Pickup
- Agents must refuse assignment if maintenance is due
- Upgrades are allowed (e.g., assign SUV when Compact requested)
- All upgrades are logged in audit trail
- Pickup is idempotent using pickup tokens

### Return
- 1-hour grace period before late fees apply
- Late fees charged per hour after grace period
- Mileage allowance: based on vehicle class daily allowance
- Fuel refill charged per 10% of tank difference
- Manual damage charges can be added by agents

### Extension
- Only allowed if no conflicting reservations exist
- Updates expected return time
- Logs extension in audit trail

### Pricing
- Composable rules via Strategy pattern
- Base rate depends on vehicle class
- Add-ons charged per day
- Insurance charged per day
- Dynamic multipliers (weekend, peak season)
- All charges itemized

### Payment
- Deposit pre-authorized at pickup
- Final payment captured at return
- Failed payments result in pending invoices
- Notifications sent for payment results

## Adding New Features

### Adding a New Pricing Rule

```python
from services.pricing_policy import PricingRule

class MyCustomRule(PricingRule):
    def calculate(self, rental_agreement, clock):
        # Your pricing logic here
        return [ChargeItem(description="...", amount=Money(...))]

# Add to policy
policy.add_rule(MyCustomRule())
```

### Adding a New Add-On

```python
airport_shuttle = AddOn(
    name="AirportShuttle",
    daily_fee=Money(Decimal('25.00'))
)

# Use in reservation
reservation = reservation_service.create_reservation(
    ...
    addons=[gps_addon, airport_shuttle],
    ...
)
```

### Adding a New Notification Type

```python
notification = Notification(
    type="CustomNotificationType",
    recipient=customer.email,
    message="Your custom message",
    timestamp=clock.now()
)
notification_port.send_notification(notification)
```

## Evaluation Criteria Compliance

✅ **OOAD Model Quality**
- All required classes modeled
- Clear relationships with multiplicities
- Principal methods documented
- UML diagram provided

✅ **SOLID Principles**
- SRP: Each service has single responsibility
- OCP: Extensible through composition
- LSP: Substitutable implementations
- ISP: Small, focused interfaces
- DIP: Depends on abstractions

✅ **Business Rules**
- ✅ Conflict detection (rental extensions)
- ✅ Maintenance holds (500km threshold)
- ✅ Grace periods (1 hour for late fees)
- ✅ Charge computation (all rules implemented)
- ✅ Idempotent operations (pickup tokens)
- ✅ Deterministic testing (injectable clock)

✅ **Code Quality**
- Type hints throughout
- Dataclasses for entities
- Clear module organization
- Comprehensive documentation
- Public APIs documented

✅ **Extensibility**
- Easy to add new pricing rules
- Easy to add new add-ons
- Easy to add new notification types
- No need to modify core classes

## License

This project is for educational purposes as part of the AIN-3005 course.

## Author

**İrem Aslan**
- Data & AI Technical Specialist Intern at Microsoft
- Senior Artificial Intelligence Engineering Student at Bahçeşehir University

**Course**: AIN-3005 Artificial Intelligence Engineering  
**Instructor**: Dr. Binnur Kurt  
**Institution**: Bahçeşehir University - AI Engineering Department
