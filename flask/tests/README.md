# Postal Code API Test Suite

This directory contains comprehensive tests for the Flask postal code API.

## Test Structure

```
tests/
├── api/                    # API integration tests
│   └── test_endpoints.py   # Tests all API endpoints
├── unit/                   # Unit tests
│   ├── test_house_number_matching.py  # House number pattern tests
│   └── test_postal_service.py         # Service layer tests
└── README.md              # This file
```

## Running Tests

### Run All Tests
```bash
python run_tests.py
```

### Run Only Unit Tests
```bash
python run_tests.py --unit-only
```

### Run Only API Tests
```bash
python run_tests.py --api-only
```

### Check Server Status
```bash
python run_tests.py --check-server
```

## Prerequisites

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **For API tests - Start the server:**
   ```bash
   python app.py
   ```
   Server should be running at http://localhost:5001

3. **Database must exist:**
   ```bash
   python create_db.py  # If database doesn't exist
   ```

## Test Coverage

### Unit Tests
- **House Number Matching**: Tests the complex Polish address pattern matching
  - Simple ranges: `"1-12"`
  - Side indicators: `"1-41(n)"` (odd), `"2-38(p)"` (even)
  - DK ranges: `"337-DK"` (open-ended)
  - Complex patterns: `"1/3-23/25(n)"`, `"4a-9/11"`

- **Postal Service**: Tests service layer functions
  - Query building logic
  - House number filtering
  - Parameter validation

### API Integration Tests
- Health endpoint
- Postal code search (basic and advanced)
- Direct postal code lookup
- Location hierarchy endpoints
- Error handling (404, etc.)
- Fallback behavior
- Parameter validation

## Example Output

```
🧪 Postal Code API Test Suite
📍 Current directory: /path/to/flask
🐍 Python version: 3.11.0

============================================================
RUNNING UNIT TESTS
============================================================

📋 Running house number matching tests...
✅ PASS - Simple ranges
✅ PASS - Side indicators
...

📊 Unit tests result: ✅ PASSED

============================================================
RUNNING API INTEGRATION TESTS
============================================================

✅ Server is running at http://localhost:5001

Testing: Health endpoint
  ✅ PASS

Testing: Basic postal code search
  ✅ PASS
...

📊 API tests result: ✅ PASSED

============================================================
TEST SUMMARY
============================================================
🎯 Overall Results:
   Total Passed: 25
   Total Failed: 0
   Total Tests:  25
   Success Rate: 100.0%
   Overall Status: ✅ ALL TESTS PASSED
```

## Troubleshooting

### API Tests Failing
- Ensure Flask server is running: `python app.py`
- Check server is accessible: `curl http://localhost:5001/health`
- Verify database exists: `ls -la postal_codes.db`

### Unit Tests Failing
- Check all Python modules are importable
- Verify house_number_matcher.py is in the correct location
- Run individual test files to isolate issues

### Import Errors
- Ensure you're running from the flask/ directory
- Check Python path includes current directory
- Verify all required dependencies are installed