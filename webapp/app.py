"""
Flask Web Application for Car Rental & Fleet Maintenance System.
Provides a web interface for managing reservations, vehicles, and rentals.
"""
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from domain.models import (
    Customer, Agent, Vehicle, VehicleClass, Location, 
    AddOn, InsuranceTier, VehicleStatus
)
from domain.value_objects import Money, FuelLevel, Kilometers
from domain.clock import SystemClock
from domain.audit_log import AuditLogger
from services.inventory_service import InventoryService
from services.maintenance_service import MaintenanceService
from services.pricing_policy import create_standard_pricing_policy
from services.rental_service import RentalService
from services.reservation_service import ReservationService
from services.accounting_service import AccountingService
from adapters.notification_port import InMemoryNotificationAdapter
from adapters.payment_port import FakePaymentAdapter

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Initialize system
clock = SystemClock()
audit_logger = AuditLogger()
notification_adapter = InMemoryNotificationAdapter(clock)
payment_adapter = FakePaymentAdapter(clock, simulate_failure=False)

maintenance_service = MaintenanceService(clock)
inventory_service = InventoryService(clock, maintenance_service)
pricing_policy = create_standard_pricing_policy(clock, apply_weekend_surcharge=True)
rental_service = RentalService(clock, pricing_policy, maintenance_service, audit_logger)
reservation_service = ReservationService(clock, notification_adapter)
accounting_service = AccountingService(clock, payment_adapter, notification_adapter)

# Create sample data
def initialize_sample_data():
    """Initialize the system with sample data."""
    global downtown_location, airport_location
    global economy_class, compact_class, suv_class
    global gps_addon, child_seat_addon, extra_driver_addon
    global basic_insurance, premium_insurance
    global sample_customer, sample_agent
    
    # Locations
    downtown_location = Location(id=1, name="Downtown Branch", address="123 Main St")
    airport_location = Location(id=2, name="Airport Branch", address="Airport Terminal 1")
    
    # Vehicle classes
    economy_class = VehicleClass(
        name="Economy",
        base_rate=Money(Decimal('50.00')),
        daily_mileage_allowance=200
    )
    compact_class = VehicleClass(
        name="Compact",
        base_rate=Money(Decimal('70.00')),
        daily_mileage_allowance=250
    )
    suv_class = VehicleClass(
        name="SUV",
        base_rate=Money(Decimal('120.00')),
        daily_mileage_allowance=300
    )
    
    # Add-ons
    gps_addon = AddOn(name="GPS", daily_fee=Money(Decimal('10.00')))
    child_seat_addon = AddOn(name="ChildSeat", daily_fee=Money(Decimal('5.00')))
    extra_driver_addon = AddOn(name="ExtraDriver", daily_fee=Money(Decimal('15.00')))
    
    # Insurance
    basic_insurance = InsuranceTier(name="Basic", daily_fee=Money(Decimal('15.00')))
    premium_insurance = InsuranceTier(name="Premium", daily_fee=Money(Decimal('30.00')))
    
    # Create vehicles
    for i in range(1, 6):
        vehicle = Vehicle(
            id=i,
            vehicle_class=economy_class if i <= 2 else (compact_class if i <= 4 else suv_class),
            location=downtown_location if i % 2 == 1 else airport_location,
            status=VehicleStatus.AVAILABLE,
            odometer=Kilometers(10000 + i * 5000),
            fuel_level=FuelLevel(0.8)
        )
        inventory_service.add_vehicle(vehicle)
    
    # Sample customer and agent
    sample_customer = Customer(
        id=1,
        name="John Doe",
        email="john.doe@example.com",
        phone="+1-555-0101"
    )
    sample_agent = Agent(id=1, name="Alice Agent", branch="Downtown")

initialize_sample_data()

@app.route('/')
def home():
    """Home page with system overview."""
    stats = inventory_service.get_vehicle_statistics()
    active_rentals = rental_service.list_active_rentals()
    overdue_rentals = rental_service.list_overdue_rentals()
    
    return render_template('home.html', 
                         stats=stats,
                         active_rentals_count=len(active_rentals),
                         overdue_rentals_count=len(overdue_rentals),
                         total_reservations=len(reservation_service.list_reservations()))

@app.route('/vehicles')
def vehicles():
    """List all vehicles."""
    all_vehicles = list(inventory_service.vehicles.values())
    return render_template('vehicles.html', vehicles=all_vehicles)

@app.route('/search', methods=['GET', 'POST'])
def search():
    """Search for available vehicles."""
    if request.method == 'POST':
        location_name = request.form.get('location')
        vehicle_class_name = request.form.get('vehicle_class')
        pickup_date = request.form.get('pickup_date')
        return_date = request.form.get('return_date')
        
        location = downtown_location if location_name == 'Downtown Branch' else airport_location
        vehicle_class = {
            'Economy': economy_class,
            'Compact': compact_class,
            'SUV': suv_class
        }.get(vehicle_class_name)
        
        pickup_dt = datetime.fromisoformat(pickup_date)
        return_dt = datetime.fromisoformat(return_date)
        
        availability = inventory_service.check_availability(
            vehicle_class, location, pickup_dt, return_dt
        )
        
        return render_template('search_results.html', 
                             availability=availability,
                             pickup_date=pickup_date,
                             return_date=return_date)
    
    return render_template('search.html',
                         locations=[downtown_location, airport_location],
                         vehicle_classes=[economy_class, compact_class, suv_class])

@app.route('/reservations')
def reservations():
    """List all reservations."""
    all_reservations = reservation_service.list_reservations()
    return render_template('reservations.html', reservations=all_reservations)

@app.route('/reservations/create', methods=['GET', 'POST'])
def create_reservation():
    """Create a new reservation."""
    if request.method == 'POST':
        vehicle_class_name = request.form.get('vehicle_class')
        location_name = request.form.get('location')
        pickup_date = request.form.get('pickup_date')
        return_date = request.form.get('return_date')
        insurance_name = request.form.get('insurance')
        addons_list = request.form.getlist('addons')
        
        vehicle_class = {
            'Economy': economy_class,
            'Compact': compact_class,
            'SUV': suv_class
        }.get(vehicle_class_name)
        
        location = downtown_location if location_name == 'Downtown Branch' else airport_location
        
        insurance = {
            'Basic': basic_insurance,
            'Premium': premium_insurance,
            'None': None
        }.get(insurance_name)
        
        addons = []
        if 'GPS' in addons_list:
            addons.append(gps_addon)
        if 'ChildSeat' in addons_list:
            addons.append(child_seat_addon)
        if 'ExtraDriver' in addons_list:
            addons.append(extra_driver_addon)
        
        pickup_dt = datetime.fromisoformat(pickup_date)
        return_dt = datetime.fromisoformat(return_date)
        
        reservation = reservation_service.create_reservation(
            customer=sample_customer,
            vehicle_class=vehicle_class,
            location=location,
            pickup_time=pickup_dt,
            return_time=return_dt,
            addons=addons,
            insurance_tier=insurance,
            deposit=Money(Decimal('200.00'))
        )
        
        return redirect(url_for('reservation_detail', reservation_id=reservation.id))
    
    return render_template('create_reservation.html',
                         locations=[downtown_location, airport_location],
                         vehicle_classes=[economy_class, compact_class, suv_class],
                         insurances=[basic_insurance, premium_insurance],
                         addons=[gps_addon, child_seat_addon, extra_driver_addon])

@app.route('/reservations/<int:reservation_id>')
def reservation_detail(reservation_id):
    """Show reservation details."""
    reservation = reservation_service.get_reservation(reservation_id)
    if not reservation:
        return "Reservation not found", 404
    return render_template('reservation_detail.html', reservation=reservation)

@app.route('/rentals')
def rentals():
    """List all rental agreements."""
    all_rentals = list(rental_service.rental_agreements.values())
    return render_template('rentals.html', rentals=all_rentals)

@app.route('/rentals/<int:rental_id>')
def rental_detail(rental_id):
    """Show rental agreement details."""
    rental = rental_service.get_rental_by_id(rental_id)
    if not rental:
        return "Rental not found", 404
    
    invoice = None
    for inv in accounting_service.invoices.values():
        if inv.rental_agreement.id == rental_id:
            invoice = inv
            break
    
    return render_template('rental_detail.html', rental=rental, invoice=invoice)

@app.route('/audit')
def audit_log():
    """Show audit log entries."""
    all_entries = audit_logger.list_all_entries()
    return render_template('audit_log.html', entries=all_entries)

@app.route('/api/stats')
def api_stats():
    """API endpoint for system statistics."""
    stats = inventory_service.get_vehicle_statistics()
    active_rentals = len(rental_service.list_active_rentals())
    overdue_rentals = len(rental_service.list_overdue_rentals())
    total_reservations = len(reservation_service.list_reservations())
    
    return jsonify({
        'fleet': stats,
        'active_rentals': active_rentals,
        'overdue_rentals': overdue_rentals,
        'total_reservations': total_reservations,
        'timestamp': clock.now().isoformat()
    })

if __name__ == "__main__":
    print("=" * 80)
    print("  Car Rental & Fleet Maintenance System - Web Interface")
    print("=" * 80)
    print("\n  🚀 Server starting...")
    print("  📍 Open your browser and navigate to: http://localhost:5000")
    print("  📊 Features available:")
    print("     - Dashboard with system overview")
    print("     - Vehicle inventory management")
    print("     - Search for available vehicles")
    print("     - Create and manage reservations")
    print("     - View rental agreements")
    print("     - Audit log viewer")
    print("     - REST API endpoints")
    print("\n  Press Ctrl+C to stop the server")
    print("=" * 80 + "\n")
    
    app.run(debug=True, port=5000)