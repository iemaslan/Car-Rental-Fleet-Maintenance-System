"""
Test Dashboard for HW2 - Car Rental & Fleet Maintenance System
Interactive web interface to run and view pytest results
"""
from flask import Flask, render_template, jsonify, request
import subprocess
import json
import os
from datetime import datetime

app = Flask(__name__, template_folder='test_templates')

# Test modules configuration
TEST_MODULES = {
    'pricing': {
        'name': 'Pricing Tests',
        'file': 'tests/test_pricing.py',
        'description': 'Base rates, addons, insurance, dynamic factors',
        'icon': '💰'
    },
    'lifecycle': {
        'name': 'Rental Lifecycle Tests',
        'file': 'tests/test_rental_lifecycle.py',
        'description': 'Pickup/return operations with idempotency',
        'icon': '🔄'
    },
    'extension': {
        'name': 'Extension & Conflicts Tests',
        'file': 'tests/test_rental_extension.py',
        'description': 'Rental extensions and conflict detection',
        'icon': '⏱️'
    },
    'maintenance': {
        'name': 'Maintenance Tests',
        'file': 'tests/test_maintenance.py',
        'description': 'Odometer and time-based maintenance',
        'icon': '🔧'
    },
    'billing': {
        'name': 'Billing & Notifications Tests',
        'file': 'tests/test_billing_notifications.py',
        'description': 'Payments, invoices, mocking',
        'icon': '💳'
    },
    'all': {
        'name': 'All Tests',
        'file': 'tests/test_pricing.py tests/test_rental_lifecycle.py tests/test_rental_extension.py tests/test_maintenance.py tests/test_billing_notifications.py',
        'description': 'Run complete test suite',
        'icon': '🎯'
    }
}

@app.route('/')
def index():
    """Dashboard home page."""
    return render_template('test_dashboard.html', modules=TEST_MODULES)

@app.route('/run-tests', methods=['POST'])
def run_tests():
    """Run pytest for selected module."""
    data = request.get_json()
    module = data.get('module', 'all')
    
    if module not in TEST_MODULES:
        return jsonify({'error': 'Invalid module'}), 400
    
    test_file = TEST_MODULES[module]['file']
    
    # Run pytest with JSON output
    cmd = [
        '.venv/bin/python', '-m', 'pytest',
        *test_file.split(),
        '-v',
        '--tb=short',
        '--json-report',
        '--json-report-file=test_results.json',
        '--json-report-indent=2'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Parse test results
        output_lines = result.stdout.split('\n')
        passed = failed = 0
        test_details = []
        
        for line in output_lines:
            if 'PASSED' in line:
                passed += 1
                test_details.append({'name': line.split('::')[1].split(' ')[0] if '::' in line else 'test', 'status': 'passed'})
            elif 'FAILED' in line:
                failed += 1
                test_details.append({'name': line.split('::')[1].split(' ')[0] if '::' in line else 'test', 'status': 'failed'})
        
        # Extract summary
        for line in output_lines:
            if 'passed' in line.lower() and ('failed' in line.lower() or line.strip().endswith('passed')):
                summary_line = line
                break
        else:
            summary_line = f"{passed} passed"
        
        return jsonify({
            'success': result.returncode == 0,
            'output': result.stdout,
            'error': result.stderr,
            'passed': passed,
            'failed': failed,
            'summary': summary_line.strip(),
            'test_details': test_details,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/run-coverage', methods=['POST'])
def run_coverage():
    """Run tests with coverage report."""
    cmd = [
        '.venv/bin/python', '-m', 'pytest',
        'tests/test_pricing.py',
        'tests/test_rental_lifecycle.py',
        'tests/test_rental_extension.py',
        'tests/test_maintenance.py',
        'tests/test_billing_notifications.py',
        '--cov=domain',
        '--cov=services',
        '--cov-report=term-missing',
        '--cov-report=html'
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        # Parse coverage from output
        coverage_lines = []
        in_coverage = False
        for line in result.stdout.split('\n'):
            if '---------- coverage:' in line:
                in_coverage = True
            if in_coverage:
                coverage_lines.append(line)
            if in_coverage and line.startswith('TOTAL'):
                break
        
        coverage_text = '\n'.join(coverage_lines)
        
        return jsonify({
            'success': result.returncode == 0,
            'coverage': coverage_text,
            'full_output': result.stdout,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test-stats')
def test_stats():
    """Get test statistics."""
    stats = {
        'total_modules': len(TEST_MODULES) - 1,  # Exclude 'all'
        'total_tests': 135,
        'parametrized_tests': 10,
        'fixtures': 30,
        'coverage': '77%'
    }
    return jsonify(stats)

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🧪 HW2 Test Dashboard Starting...")
    print("="*60)
    print("\n📊 Dashboard URL: http://127.0.0.1:5002")
    print("\n✨ Features:")
    print("  • Run tests by category")
    print("  • View real-time results")
    print("  • Check coverage reports")
    print("  • Interactive test management")
    print("\n" + "="*60 + "\n")
    
    app.run(debug=True, port=5002)
