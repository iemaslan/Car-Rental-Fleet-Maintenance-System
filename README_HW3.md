# Homework 3: File Operations & Protocol Buffers

**Course:** AIN-3005 Advanced Python Programming  
**Student:** İrem Aslan  
**Student ID:** 2101956  
**Due Date:** December 19, 2024

## 📋 Overview

This homework demonstrates advanced file operations in Python using both JSON and Protocol Buffers for serializing and deserializing the Car Rental & Fleet Maintenance System (CRFMS) state.

## 🎯 Requirements Compliance

### ✅ Core Requirements

1. **JSON Persistence** ✓
   - Implemented `persistence/json_persistence.py`
   - `save_snapshot()` - saves complete system state to JSON
   - `load_snapshot()` - loads system state from JSON
   - Uses context managers (`with open()`)
   - Proper file modes: `'rt'` (read text), `'wt'` (write text)
   - UTF-8 encoding specified
   - Error handling for missing/malformed files

2. **Protocol Buffers Schema** ✓
   - Created `persistence/crfms.proto`
   - Defined messages for all domain entities:
     - Customer, Vehicle, VehicleClass, Location
     - Reservation, RentalAgreement
     - MaintenanceRecord, Invoice, Payment, Notification
     - AuditEntry
   - Root `CrfmsSnapshot` message with repeated fields
   - Value objects: Money, Kilometers, FuelLevel
   - Compiled to `crfms_pb2.py` using `protoc`

3. **Protobuf Serialization** ✓
   - Implemented `persistence/protobuf_persistence.py`
   - `save_snapshot()` - serializes to binary format
   - `load_snapshot()` - deserializes from binary
   - Uses proper file modes: `'rb'` (read binary), `'wb'` (write binary)
   - Conversion methods for all domain objects

4. **Format Conversion Utility** ✓
   - Created `convert_format.py` CLI script
   - Bidirectional conversion:
     - `--to-proto` - JSON → Protobuf
     - `--to-json` - Protobuf → JSON
   - Command-line arguments with `argparse`
   - Proper error handling and user feedback
   - Executable script with shebang

5. **File-Based Reporting** ✓
   - Created `generate_report.py` script
   - Loads snapshots from either JSON or Protobuf files
   - Auto-detects file format
   - Generates comprehensive aggregate reports:
     - Customer statistics
     - Vehicle fleet analytics (by class, status, mileage)
     - Reservation breakdown
     - Active vs completed rentals
     - Revenue metrics
     - Maintenance tracking
     - Invoice and payment summaries
     - Notification stats
   - Pretty-printed output to stdout

6. **Documentation** ✓
   - This README with complete instructions
   - Code comments and docstrings
   - Usage examples

### ✅ Technical Requirements

- **File Operations**: ✓
  - Context managers (`with open()`)
  - Correct file modes (`'rt'`, `'wt'`, `'rb'`, `'wb'`)
  - UTF-8 encoding for text files
  - Binary mode for Protocol Buffers

- **Error Handling**: ✓
  - `FileNotFoundError` for missing files
  - `json.JSONDecodeError` for malformed JSON
  - Graceful error messages to stderr
  - Exit codes for CLI scripts

- **Code Quality**: ✓
  - Type hints
  - Docstrings for all functions
  - Clean separation of concerns
  - DRY principle

## 🚀 Installation

### Prerequisites

```bash
# Install Protocol Buffers compiler (macOS)
brew install protobuf

# For Linux
sudo apt-get install protobuf-compiler

# For Windows
choco install protobuf
```

### Python Dependencies

```bash
# Install required packages
pip install protobuf

# Or use requirements.txt
pip install -r requirements.txt
```

### Compile Protocol Buffers Schema

```bash
cd persistence
protoc --python_out=. crfms.proto
```

This generates `crfms_pb2.py` containing Python classes for all message types.

## 📖 Usage

### 1. JSON Persistence

#### Save Snapshot to JSON

```python
from persistence.json_persistence import JSONPersistence

# Assuming you have domain objects loaded
JSONPersistence.save_snapshot(
    filename='snapshots/crfms_snapshot.json',
    customers=customers_list,
    vehicles=vehicles_list,
    reservations=reservations_list,
    rental_agreements=rental_agreements_list,
    maintenance_records=maintenance_records_list,
    invoices=invoices_list,
    payments=payments_list,
    notifications=notifications_list
)
```

#### Load Snapshot from JSON

```python
from persistence.json_persistence import JSONPersistence

try:
    data = JSONPersistence.load_snapshot('snapshots/crfms_snapshot.json')
    customers = data['customers']
    vehicles = data['vehicles']
    # ... process data
except FileNotFoundError:
    print("Snapshot file not found")
except json.JSONDecodeError:
    print("Invalid JSON format")
```

### 2. Protocol Buffers Persistence

#### Save Snapshot to Protobuf

```python
from persistence.protobuf_persistence import ProtobufPersistence

ProtobufPersistence.save_snapshot(
    filename='snapshots/crfms_snapshot.pb',
    customers=customers_list,
    vehicles=vehicles_list,
    reservations=reservations_list,
    rental_agreements=rental_agreements_list,
    maintenance_records=maintenance_records_list,
    invoices=invoices_list,
    payments=payments_list,
    notifications=notifications_list
)
```

#### Load Snapshot from Protobuf

```python
from persistence.protobuf_persistence import ProtobufPersistence

try:
    data = ProtobufPersistence.load_snapshot('snapshots/crfms_snapshot.pb')
    # data contains protobuf message objects
except FileNotFoundError:
    print("Snapshot file not found")
```

### 3. Format Conversion

#### Convert JSON to Protobuf

```bash
python convert_format.py \
    --input snapshots/crfms_snapshot.json \
    --output snapshots/crfms_snapshot.pb \
    --to-proto
```

#### Convert Protobuf to JSON

```bash
python convert_format.py \
    --input snapshots/crfms_snapshot.pb \
    --output snapshots/crfms_snapshot.json \
    --to-json
```

#### Help

```bash
python convert_format.py --help
```

### 4. Generate Reports

```bash
# From JSON file
python generate_report.py snapshots/crfms_snapshot.json

# From Protobuf file
python generate_report.py snapshots/crfms_snapshot.pb

# Auto-detect format
python generate_report.py snapshots/my_snapshot
```

#### Sample Report Output

```
======================================================================
CRFMS SYSTEM REPORT
======================================================================

Snapshot Version: 1.0
Generated: 2024-12-11T10:30:45

📊 CUSTOMER STATISTICS
   Total Customers: 25

🚗 VEHICLE FLEET STATISTICS
   Total Vehicles: 50
   Total Fleet Mileage: 1,250,000 km
   Average Mileage per Vehicle: 25,000 km

   Vehicles by Class:
      • COMPACT: 15
      • LUXURY: 10
      • SEDAN: 15
      • SUV: 10

   Vehicles by Status:
      • AVAILABLE: 35
      • MAINTENANCE: 3
      • RENTED: 12

📅 RESERVATION STATISTICS
   Total Reservations: 45
   Reservations by Vehicle Class:
      • COMPACT: 12
      • LUXURY: 8
      • SEDAN: 15
      • SUV: 10

🔑 RENTAL AGREEMENT STATISTICS
   Total Rentals: 40
   Active Rentals: 12
   Completed Rentals: 28
   Total Revenue from Rentals: $45,678.50
   Average Revenue per Completed Rental: $1,631.38

🔧 MAINTENANCE STATISTICS
   Total Maintenance Records: 15
   Maintenance by Service Type:
      • OIL_CHANGE: 8
      • TIRE_ROTATION: 5
      • INSPECTION: 2

📄 INVOICE STATISTICS
   Total Invoices: 40
   Total Invoiced Amount: $48,920.75
   Average Invoice Amount: $1,223.02
   Invoices by Status:
      • PAID: 28
      • PENDING: 10
      • OVERDUE: 2

💳 PAYMENT STATISTICS
   Total Payments: 35
   Total Amount Paid: $42,150.00
   Average Payment Amount: $1,204.29
   Payments by Status:
      • COMPLETED: 32
      • PENDING: 3

🔔 NOTIFICATION STATISTICS
   Total Notifications: 120
   Sent: 115
   Pending: 5

======================================================================
```

## 📁 Project Structure

```
Car-Rental-Fleet-Maintenance-System/
├── persistence/
│   ├── __init__.py                 # Persistence module init
│   ├── json_persistence.py         # JSON save/load implementation
│   ├── protobuf_persistence.py     # Protobuf save/load implementation
│   ├── crfms.proto                 # Protocol Buffers schema definition
│   └── crfms_pb2.py                # Generated Python protobuf classes
├── convert_format.py               # CLI format conversion utility
├── generate_report.py              # File-based reporting script
├── README_HW3.md                   # This file
└── snapshots/                      # Directory for snapshot files
    ├── *.json                      # JSON snapshots
    └── *.pb                        # Protobuf snapshots
```

## 🔧 Technical Details

### File Modes Used

| Operation | Format | Mode | Encoding |
|-----------|--------|------|----------|
| Save JSON | Text | `'wt'` | UTF-8 |
| Load JSON | Text | `'rt'` | UTF-8 |
| Save Protobuf | Binary | `'wb'` | N/A |
| Load Protobuf | Binary | `'rb'` | N/A |

### Error Handling Examples

```python
# JSON loading with error handling
try:
    data = JSONPersistence.load_snapshot('file.json')
except FileNotFoundError:
    print("File doesn't exist")
except json.JSONDecodeError as e:
    print(f"Malformed JSON: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Context Managers

All file operations use context managers to ensure proper resource cleanup:

```python
# Automatically closes file even if exception occurs
with open(filename, mode='wt', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
```

## 🧪 Testing

### Create Test Snapshot

```python
# Run the demo to generate sample data
python demo.py

# This will create sample JSON and Protobuf snapshots
```

### Verify Conversion

```bash
# Convert JSON → Protobuf → JSON
python convert_format.py -i test.json -o test.pb --to-proto
python convert_format.py -i test.pb -o test2.json --to-json

# Compare original and converted
diff test.json test2.json
```

### Test Report Generation

```bash
# Generate report from both formats
python generate_report.py test.json > report_json.txt
python generate_report.py test.pb > report_pb.txt

# Should produce identical reports
diff report_json.txt report_pb.txt
```

## 💡 Key Features

1. **Comprehensive Serialization**
   - All domain entities serializable
   - Nested objects properly handled
   - Optional fields supported
   - Metadata included in snapshots

2. **Robust Error Handling**
   - Descriptive error messages
   - Proper exception types
   - Exit codes for CLI tools
   - User-friendly feedback

3. **Flexible Format Support**
   - JSON for human readability
   - Protobuf for efficiency and type safety
   - Seamless bidirectional conversion
   - Auto-detection in reporting

4. **Production-Ready Code**
   - Type hints throughout
   - Comprehensive docstrings
   - Clean architecture
   - Separation of concerns

## 🎓 Learning Outcomes

This assignment demonstrates:

- ✅ Advanced file I/O operations
- ✅ Context managers and resource management
- ✅ Text vs binary file modes
- ✅ JSON serialization/deserialization
- ✅ Protocol Buffers schema design
- ✅ Binary serialization formats
- ✅ CLI tool development with argparse
- ✅ Error handling and exceptions
- ✅ Data aggregation and reporting
- ✅ Code organization and modularity

## 📚 References

- [Python File I/O Documentation](https://docs.python.org/3/tutorial/inputoutput.html#reading-and-writing-files)
- [JSON Module](https://docs.python.org/3/library/json.html)
- [Protocol Buffers Python Tutorial](https://protobuf.dev/getting-started/pythontutorial/)
- [argparse Documentation](https://docs.python.org/3/library/argparse.html)

## 👤 Author

**İrem Aslan**  
Student ID: 2101956  
AIN-3005 Advanced Python Programming  
December 2024

---

**Note:** All code follows PEP 8 style guidelines and includes comprehensive error handling for production use.
