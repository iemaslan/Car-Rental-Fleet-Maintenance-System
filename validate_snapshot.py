#!/usr/bin/env python3
"""
Validate CRFMS Snapshot with Progress Bar.
Validates JSON snapshot files for schema and business rule compliance.

Usage:
    python validate_snapshot.py snapshot.json
"""
import argparse
import json
import sys
from pathlib import Path
import time

from persistence.json_schema import JSONSchemaValidator, ValidationError
from persistence.business_rules import BusinessRuleValidator, BusinessRuleViolation

# ANSI color codes
class Colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    CYAN = '\033[96m'

def colored_print(message: str, color: str = Colors.ENDC) -> None:
    """Print colored message."""
    print(f"{color}{message}{Colors.ENDC}")

def progress_bar(current: int, total: int, prefix: str = '', length: int = 40):
    """Display a progress bar."""
    percent = current / total if total > 0 else 0
    filled_length = int(length * percent)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent*100:.1f}% ({current}/{total})', end='', flush=True)
    if current == total:
        print()  # New line when complete

def validate_snapshot(filename: str) -> None:
    """Validate a snapshot file with progress indication."""
    colored_print(f"\n{'='*70}", Colors.BOLD)
    colored_print(f"  CRFMS Snapshot Validator", Colors.CYAN + Colors.BOLD)
    colored_print(f"{'='*70}\n", Colors.BOLD)
    
    colored_print(f"📂 Loading snapshot: {filename}", Colors.CYAN)
    
    try:
        with open(filename, 'rt', encoding='utf-8') as f:
            snapshot = json.load(f)
        
        colored_print(f"✓ File loaded successfully\n", Colors.OKGREEN)
        
        # Count total validation steps
        total_steps = 0
        if 'customers' in snapshot:
            total_steps += len(snapshot['customers'])
        if 'vehicles' in snapshot:
            total_steps += len(snapshot['vehicles'])
        if 'reservations' in snapshot:
            total_steps += len(snapshot['reservations'])
        if 'rental_agreements' in snapshot:
            total_steps += len(snapshot['rental_agreements'])
        if 'invoices' in snapshot:
            total_steps += len(snapshot['invoices'])
        
        colored_print("🔍 Performing Schema Validation...", Colors.CYAN)
        
        # Simulate progressive validation for visual feedback
        current_step = 0
        
        # Validate customers
        if 'customers' in snapshot:
            for i, customer in enumerate(snapshot['customers'], 1):
                JSONSchemaValidator.validate_customer(customer, i)
                current_step += 1
                progress_bar(current_step, total_steps, prefix='Validating')
                time.sleep(0.01)  # Small delay for visibility
        
        # Validate vehicles
        if 'vehicles' in snapshot:
            for i, vehicle in enumerate(snapshot['vehicles'], 1):
                JSONSchemaValidator.validate_vehicle(vehicle, i)
                current_step += 1
                progress_bar(current_step, total_steps, prefix='Validating')
                time.sleep(0.01)
        
        # Validate reservations
        if 'reservations' in snapshot:
            for i, reservation in enumerate(snapshot['reservations'], 1):
                JSONSchemaValidator.validate_reservation(reservation, i)
                current_step += 1
                progress_bar(current_step, total_steps, prefix='Validating')
                time.sleep(0.01)
        
        # Validate rental agreements
        if 'rental_agreements' in snapshot:
            for i, rental in enumerate(snapshot['rental_agreements'], 1):
                JSONSchemaValidator.validate_rental_agreement(rental, i)
                current_step += 1
                progress_bar(current_step, total_steps, prefix='Validating')
                time.sleep(0.01)
        
        # Validate invoices
        if 'invoices' in snapshot:
            for i, invoice in enumerate(snapshot['invoices'], 1):
                JSONSchemaValidator.validate_invoice(invoice, i)
                current_step += 1
                progress_bar(current_step, total_steps, prefix='Validating')
                time.sleep(0.01)
        
        # Get all schema errors
        schema_errors = JSONSchemaValidator.validate_snapshot(snapshot)
        
        if schema_errors:
            colored_print(f"\n\n✗ Schema Validation Failed ({len(schema_errors)} errors):", Colors.FAIL)
            for error in schema_errors:
                colored_print(f"  • {error}", Colors.WARNING)
            sys.exit(1)
        
        colored_print(f"\n✓ Schema validation passed\n", Colors.OKGREEN)
        
        # Business rules validation
        colored_print("🔍 Performing Business Rules Validation...", Colors.CYAN)
        progress_bar(0, 1, prefix='Checking business rules')
        time.sleep(0.1)
        
        business_errors = BusinessRuleValidator.validate_snapshot(snapshot)
        progress_bar(1, 1, prefix='Checking business rules')
        
        if business_errors:
            colored_print(f"\n\n⚠ Business Rule Violations ({len(business_errors)}):", Colors.WARNING)
            for error in business_errors:
                colored_print(f"  • {error}", Colors.WARNING)
            colored_print("\nNote: These are warnings. Data structure is valid but business rules are violated.\n", Colors.WARNING)
        else:
            colored_print(f"\n✓ All business rules passed\n", Colors.OKGREEN)
        
        # Summary
        colored_print(f"{'='*70}", Colors.BOLD)
        colored_print(f"  VALIDATION SUMMARY", Colors.CYAN + Colors.BOLD)
        colored_print(f"{'='*70}", Colors.BOLD)
        colored_print(f"  Customers:          {len(snapshot.get('customers', []))}", Colors.ENDC)
        colored_print(f"  Vehicles:           {len(snapshot.get('vehicles', []))}", Colors.ENDC)
        colored_print(f"  Reservations:       {len(snapshot.get('reservations', []))}", Colors.ENDC)
        colored_print(f"  Rental Agreements:  {len(snapshot.get('rental_agreements', []))}", Colors.ENDC)
        colored_print(f"  Invoices:           {len(snapshot.get('invoices', []))}", Colors.ENDC)
        colored_print(f"  Schema Errors:      {len(schema_errors)}", Colors.OKGREEN if not schema_errors else Colors.FAIL)
        colored_print(f"  Rule Violations:    {len(business_errors)}", Colors.OKGREEN if not business_errors else Colors.WARNING)
        colored_print(f"{'='*70}\n", Colors.BOLD)
        
        if not schema_errors and not business_errors:
            colored_print("  ✨ Snapshot is VALID and ready for production! ✨\n", Colors.OKGREEN + Colors.BOLD)
        elif not schema_errors:
            colored_print("  ⚠ Snapshot structure is valid but has business rule warnings\n", Colors.WARNING + Colors.BOLD)
        
    except FileNotFoundError:
        colored_print(f"✗ Error: File not found: {filename}", Colors.FAIL)
        sys.exit(1)
    except json.JSONDecodeError as e:
        colored_print(f"✗ Error: Invalid JSON file: {e}", Colors.FAIL)
        sys.exit(1)
    except Exception as e:
        colored_print(f"✗ Error: {e}", Colors.FAIL)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='Validate CRFMS snapshot files for schema and business rule compliance',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s snapshot.json
  %(prog)s snapshots/test_snapshot.json
        '''
    )
    
    parser.add_argument('input', help='Input snapshot file (JSON)')
    
    args = parser.parse_args()
    
    if not Path(args.input).exists():
        colored_print(f"✗ Error: File not found: {args.input}", Colors.FAIL)
        sys.exit(1)
    
    validate_snapshot(args.input)

if __name__ == '__main__':
    main()
