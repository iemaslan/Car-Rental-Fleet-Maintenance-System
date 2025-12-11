"""
Snapshot Viewer Web Application
Displays JSON and Protobuf snapshot data in a user-friendly interface
"""
from flask import Flask, render_template, request, jsonify
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from persistence import crfms_pb2

app = Flask(__name__)
app.secret_key = 'hw3-snapshot-viewer'

SNAPSHOT_DIR = os.path.join(os.path.dirname(__file__), '..', 'snapshots')


def load_json_snapshot(filepath):
    """Load and parse JSON snapshot file."""
    try:
        with open(filepath, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        return data, None
    except FileNotFoundError:
        return None, "File not found"
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e.msg}"
    except Exception as e:
        return None, f"Error: {str(e)}"


def load_proto_snapshot(filepath):
    """Load and parse Protocol Buffers snapshot file."""
    try:
        snapshot = crfms_pb2.CrfmsSnapshot()
        with open(filepath, 'rb') as f:
            snapshot.ParseFromString(f.read())
        
        # Convert to dictionary for easier template rendering
        data = {
            'metadata': {
                'version': snapshot.metadata.version,
                'timestamp': snapshot.metadata.timestamp,
                'description': snapshot.metadata.description
            },
            'customers': [
                {
                    'id': c.id,
                    'name': c.name,
                    'email': c.email,
                    'phone': c.phone
                }
                for c in snapshot.customers
            ],
            'vehicles': [
                {
                    'id': v.id,
                    'vehicle_class': v.vehicle_class.name,
                    'location': v.location.name,
                    'status': v.status,
                    'odometer': v.odometer.value,
                    'fuel_level': v.fuel_level.level
                }
                for v in snapshot.vehicles
            ],
            'reservations': [
                {
                    'id': r.id,
                    'customer_id': r.customer_id,
                    'vehicle_class_name': r.vehicle_class_name,
                    'location_id': r.location_id,
                    'pickup_time': r.pickup_time,
                    'return_time': r.return_time
                }
                for r in snapshot.reservations
            ],
            'rental_agreements': [
                {
                    'id': ra.id,
                    'reservation_id': ra.reservation_id,
                    'vehicle_id': ra.vehicle_id,
                    'pickup_token': ra.pickup_token,
                    'start_odometer': ra.start_odometer.value,
                    'end_odometer': ra.end_odometer.value if ra.HasField('end_odometer') else None,
                    'pickup_time': ra.pickup_time,
                    'expected_return_time': ra.expected_return_time,
                    'actual_return_time': ra.actual_return_time if ra.actual_return_time else None
                }
                for ra in snapshot.rental_agreements
            ],
            'maintenance_records': [
                {
                    'id': m.id,
                    'vehicle_id': m.vehicle_id,
                    'service_type': m.service_type,
                    'odometer_threshold': m.odometer_threshold.value,
                    'last_service_date': m.last_service_date if m.last_service_date else None
                }
                for m in snapshot.maintenance_records
            ],
            'invoices': [
                {
                    'id': inv.id,
                    'rental_agreement_id': inv.rental_agreement_id,
                    'total_amount': inv.total_amount.amount,
                    'status': inv.status,
                    'created_at': inv.created_at
                }
                for inv in snapshot.invoices
            ],
            'payments': [
                {
                    'id': p.id,
                    'invoice_id': p.invoice_id,
                    'amount': p.amount.amount,
                    'status': p.status,
                    'timestamp': p.timestamp
                }
                for p in snapshot.payments
            ],
            'notifications': [
                {
                    'type': n.type,
                    'recipient': n.recipient,
                    'message': n.message,
                    'timestamp': n.timestamp
                }
                for n in snapshot.notifications
            ]
        }
        return data, None
    except FileNotFoundError:
        return None, "File not found"
    except Exception as e:
        return None, f"Error: {str(e)}"


def calculate_statistics(data):
    """Calculate aggregate statistics from snapshot data."""
    stats = {}
    
    # Customer stats
    stats['total_customers'] = len(data.get('customers', []))
    
    # Vehicle stats
    vehicles = data.get('vehicles', [])
    stats['total_vehicles'] = len(vehicles)
    stats['available_vehicles'] = sum(1 for v in vehicles if v.get('status') == 'AVAILABLE')
    stats['rented_vehicles'] = sum(1 for v in vehicles if v.get('status') == 'RENTED')
    stats['maintenance_vehicles'] = sum(1 for v in vehicles if v.get('status') == 'MAINTENANCE')
    
    # Reservation stats
    stats['total_reservations'] = len(data.get('reservations', []))
    
    # Rental stats
    rentals = data.get('rental_agreements', [])
    stats['total_rentals'] = len(rentals)
    stats['active_rentals'] = sum(1 for r in rentals if not r.get('actual_return_time'))
    stats['completed_rentals'] = sum(1 for r in rentals if r.get('actual_return_time'))
    
    # Invoice stats
    invoices = data.get('invoices', [])
    stats['total_invoices'] = len(invoices)
    stats['paid_invoices'] = sum(1 for i in invoices if i.get('status') == 'PAID')
    stats['pending_invoices'] = sum(1 for i in invoices if i.get('status') == 'PENDING')
    stats['total_revenue'] = sum(i.get('total_amount', 0) for i in invoices)
    
    # Payment stats
    payments = data.get('payments', [])
    stats['total_payments'] = len(payments)
    stats['completed_payments'] = sum(1 for p in payments if p.get('status') == 'COMPLETED')
    stats['total_paid'] = sum(p.get('amount', 0) for p in payments if p.get('status') == 'COMPLETED')
    
    # Maintenance stats
    stats['total_maintenance'] = len(data.get('maintenance_records', []))
    
    # Notification stats
    stats['total_notifications'] = len(data.get('notifications', []))
    
    return stats


@app.route('/')
def index():
    """Home page with file selection."""
    # List available snapshot files
    json_files = []
    proto_files = []
    
    if os.path.exists(SNAPSHOT_DIR):
        for filename in os.listdir(SNAPSHOT_DIR):
            filepath = os.path.join(SNAPSHOT_DIR, filename)
            if os.path.isfile(filepath):
                if filename.endswith('.json'):
                    json_files.append(filename)
                elif filename.endswith('.pb'):
                    proto_files.append(filename)
    
    return render_template('snapshot_index.html', 
                         json_files=json_files, 
                         proto_files=proto_files)


@app.route('/view/<file_type>/<filename>')
def view_snapshot(file_type, filename):
    """View snapshot data."""
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    
    if file_type == 'json':
        data, error = load_json_snapshot(filepath)
    elif file_type == 'proto':
        data, error = load_proto_snapshot(filepath)
    else:
        return "Invalid file type", 400
    
    if error:
        return f"Error loading file: {error}", 500
    
    stats = calculate_statistics(data)
    
    return render_template('snapshot_viewer.html',
                         filename=filename,
                         file_type=file_type.upper(),
                         data=data,
                         stats=stats)


@app.route('/api/snapshot/<file_type>/<filename>')
def api_snapshot(file_type, filename):
    """API endpoint to get snapshot data as JSON."""
    filepath = os.path.join(SNAPSHOT_DIR, filename)
    
    if file_type == 'json':
        data, error = load_json_snapshot(filepath)
    elif file_type == 'proto':
        data, error = load_proto_snapshot(filepath)
    else:
        return jsonify({'error': 'Invalid file type'}), 400
    
    if error:
        return jsonify({'error': error}), 500
    
    stats = calculate_statistics(data)
    
    return jsonify({
        'data': data,
        'stats': stats
    })


@app.route('/compare')
def compare_snapshots():
    """Compare JSON and Protobuf file sizes."""
    comparisons = []
    
    if os.path.exists(SNAPSHOT_DIR):
        # Find matching JSON and PB files
        json_files = {f[:-5]: f for f in os.listdir(SNAPSHOT_DIR) if f.endswith('.json')}
        
        for base_name, json_file in json_files.items():
            pb_file = base_name + '.pb'
            pb_path = os.path.join(SNAPSHOT_DIR, pb_file)
            json_path = os.path.join(SNAPSHOT_DIR, json_file)
            
            if os.path.exists(pb_path):
                json_size = os.path.getsize(json_path)
                pb_size = os.path.getsize(pb_path)
                savings = json_size - pb_size
                savings_pct = (savings / json_size * 100) if json_size > 0 else 0
                
                comparisons.append({
                    'name': base_name,
                    'json_file': json_file,
                    'pb_file': pb_file,
                    'json_size': json_size,
                    'pb_size': pb_size,
                    'savings': savings,
                    'savings_pct': savings_pct
                })
    
    return render_template('snapshot_compare.html', comparisons=comparisons)


if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 Snapshot Viewer Starting...")
    print("="*70)
    print(f"📁 Snapshot Directory: {SNAPSHOT_DIR}")
    print(f"🌐 Server: http://127.0.0.1:5000")
    print("="*70 + "\n")
    app.run(debug=True, port=5000)
