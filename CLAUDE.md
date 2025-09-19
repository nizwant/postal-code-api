# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-technology API performance comparison project for Polish postal code lookups. The project contains separate implementations in different frameworks/languages (Flask, FastAPI, Elixir, Go) to compare performance across technologies.

## Architecture

### Data Source
- **Source**: `postal_codes_poland.csv` (7.1MB, 117k records)
- **Schema**: PNA (postal code), Miejscowość (city), Ulica (street), Numery (house numbers), Gmina (municipality), Powiat (county), Województwo (province)

### Implementation Structure
Each technology implementation is in its own directory:
- `flask/` - Flask + SQLite implementation (complete with modular architecture)
- `fastapi/` - FastAPI + SQLite implementation (complete, mirrors Flask functionality)
- `elixir/` - Elixir implementation (placeholder)
- `go/` - Go implementation (placeholder)

### Shared Database
- **Database**: `postal_codes.db` (31MB, 122k normalized records) in project root
- **Creation Script**: `create_db.py` (352 lines) in project root - run once for all implementations
- **CSV Source**: `postal_codes_poland.csv` (7.1MB original data) in project root
- **Polish Character Support**: Normalized columns with ASCII equivalents for better search performance

### Flask Implementation Details
- **Database**: **Normalized SQLite** - comma-separated house number ranges split into individual records
  - Original: 117,679 records with comma-separated patterns like `"270-336(p), 283-335(n)"`
  - Normalized: 122,765 records (1.04x growth) with individual patterns like `"270-336(p)"` and `"283-335(n)"`
  - Full indexing on all searchable fields for optimal performance
- **House Number Matching**: **Sophisticated pattern engine** (`house_number_matcher.py`) supporting Polish addressing conventions:
  - Simple ranges: `"1-12"`
  - Side indicators: `"1-41(n)"` (nieparzyste/odd), `"2-38(p)"` (parzyste/even)
  - Open-ended ranges: `"337-DK"` (do końca/to infinity), `"2-DK(p)"`
  - Letter suffixes: `"4a-9/11"`, `"31-31a"`, `"22-22b"`
  - Complex slash notation: `"1/3-23/25(n)"`, `"55-69/71(n)"`, `"2/4-10(p)"`
  - Individual numbers: `"60"`, `"35c"`
- **Search Strategy**: Hybrid approach - SQL pre-filtering + Python pattern matching
  - SQL handles city/street/location filtering with indexes
  - Python handles complex house number pattern matching (0.01ms per record)
- **API Pattern**: RESTful with hierarchical location endpoints + enhanced full address lookup
- **Fallback Logic**: Intelligent cascading search fallbacks (house_number → street → city-only)
- **Production Server**: Gunicorn with multiple workers
- **Code Architecture**: Modular design with separated concerns:
  - `app.py` - Flask application bootstrap and database validation
  - `routes.py` - API endpoint definitions and request handling
  - `postal_service.py` - Core search logic and database queries
  - `house_number_matcher.py` - Dedicated pattern matching engine
  - `polish_normalizer.py` - Polish character normalization utilities
  - `database.py` - Database connection utilities
  - `../create_db.py` - Database normalization and creation (project root)
  - `tests/` - Comprehensive test suite with API and unit tests
  - `run_tests.py` - Test runner with detailed output

### FastAPI Implementation Details
- **Architecture**: Mirrors Flask implementation with FastAPI-specific patterns
- **Code Structure**: Modular design matching Flask:
  - `main.py` - FastAPI application with startup validation
  - `app.py` - Gunicorn entry point for production deployment
  - `routes.py` - FastAPI router with type hints and automatic docs
  - `postal_service.py` - Shared core search logic (identical to Flask)
  - `house_number_matcher.py` - Shared pattern matching engine
  - `polish_normalizer.py` - Shared normalization utilities
  - `database.py` - Shared database connection utilities
  - `test_basic.py` - Basic API validation tests
- **Features**: Automatic OpenAPI docs, type validation, async support ready
- **Production Server**: Gunicorn with Uvicorn workers

## Common Development Commands

### Project Setup
```bash
# Install dependencies (Poetry managed)
poetry install

# For Flask specifically
cd flask
pip install -r requirements.txt
```

### FastAPI Development
```bash
# Create/recreate normalized database from CSV (run once from project root)
python create_db.py

# Then start FastAPI development
cd fastapi

# Development server (localhost:5002)
python main.py

# Production server (recommended for testing)
pip install uvicorn[standard] gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5002

# Test API - Basic endpoints
curl "http://localhost:5002/health"
curl "http://localhost:5002/docs"  # Automatic OpenAPI documentation

# Run basic tests
python test_basic.py
```

### Flask Development
```bash
# Create/recreate normalized database from CSV (run once from project root)
python create_db.py

# Then start Flask development
cd flask

# Development server (localhost:5001)
python app.py

# Production server (recommended for testing)
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5001 app:app

# Test API - Basic endpoints
curl "http://localhost:5001/health"
curl "http://localhost:5001/locations/provinces"

# Test full address lookup (NEW FEATURE)
curl "http://localhost:5001/postal-codes?city=Warszawa&street=Edwarda%20Józefa%20Abramowskiego&house_number=5"
# Returns: 02-659 (matches range "1-19(n)" for odd numbers)

curl "http://localhost:5001/postal-codes?city=Warszawa&street=Edwarda%20Józefa%20Abramowskiego&house_number=6"
# Returns: 02-659 (matches range "2-16a(p)" for even numbers)

# Run comprehensive test suite
python run_tests.py
```

## API Design Patterns

### Search Endpoints
All implementations should follow this pattern:
- `GET /postal-codes` - Multi-parameter search (city, street, house_number, province, county, municipality, limit)
- `GET /postal-codes/{code}` - Direct postal code lookup

### Location Hierarchy Endpoints
- `GET /locations` - Available endpoints directory
- `GET /locations/provinces?prefix=X` - All provinces, optionally filtered by prefix
- `GET /locations/counties?province=X&prefix=Y` - Counties, optionally filtered by province and prefix
- `GET /locations/municipalities?province=X&county=Y&prefix=Z` - Municipalities, optionally filtered
- `GET /locations/cities?province=X&county=Y&municipality=Z&prefix=W` - Cities, optionally filtered

### Additional Endpoints
- `GET /health` - Health check endpoint for monitoring

### Search Behavior Requirements
- **City matching**: Partial matching (e.g., "Warszawa" matches "Warszawa (Mokotów)")
- **Other fields**: Exact matching, case-insensitive
- **house_number**: **ENHANCED** - Sophisticated pattern matching against normalized ranges:
  - Handles Polish addressing patterns: `"1-19(n)"`, `"2-38(p)"`, `"337-DK"`, `"4a-9/11"`
  - Uses dedicated pattern matching engine (`house_number_matcher.py`)
  - Performance: 0.01ms per pattern evaluation
- **Fallback logic**: Intelligent cascading search fallbacks when no results found:
  1. Remove house_number parameter if present
  2. Remove street parameter if still no results
  3. Falls back to city-only search for broader results
- **Results**: Limited by `limit` parameter (default 100, minimum 1)
- **Polish characters**: Full support via URL encoding and normalized search columns
- **Prefix searching**: All location hierarchy endpoints support prefix-based filtering for autocomplete functionality

## Production Deployment Commands

For fair performance comparison, each technology must use production-grade servers:

### Flask (Port 5001)
```bash
cd flask
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5001 app:app
```

### FastAPI (Port 5002)
```bash
cd fastapi
pip install uvicorn[standard] gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5002
```

### Go (Port 5003)
```bash
cd go
go build -o postal-api main.go
./postal-api  # Built-in production server
```

### Elixir (Port 5004)
```bash
cd elixir
MIX_ENV=prod mix deps.get
MIX_ENV=prod mix phx.server  # Phoenix production server
```

## Testing Infrastructure

The project includes comprehensive testing tools:

### Comprehensive Test Suite
- **Location**: `postal_api_test_suite.py` (1,135+ lines) in project root
- **Purpose**: Ultimate testing solution for Polish postal code APIs
- **Features**:
  - Complete pipeline validation (CSV → Database → API responses)
  - Human behavior simulation and cross-API validation
  - Support for testing individual APIs or all APIs simultaneously
  - Multiple test categories: core, human behavior, edge cases, performance
  - Detailed JSON result export capability

### Test Suite Usage
```bash
# Test all APIs (full suite)
python3 postal_api_test_suite.py

# Test specific API implementation
python3 postal_api_test_suite.py --api flask
python3 postal_api_test_suite.py --port 5003  # For Go implementation

# Quick core tests only
python3 postal_api_test_suite.py --quick

# Specialized test runs
python3 postal_api_test_suite.py --csv-tests     # CSV validation only
python3 postal_api_test_suite.py --human-tests  # Human behavior simulation
python3 postal_api_test_suite.py --save-results # Export detailed JSON
```

## Performance Considerations

The goal is API performance comparison, so:
- **Production servers required** - No development servers for benchmarking
- Database choice should optimize for read performance
- **Database normalization**: 117k → 122k records (1.04x growth) for enhanced functionality
- **Hybrid approach**: SQL pre-filtering + Python pattern matching for optimal performance
- House number pattern matching: 0.01ms per record evaluation
- Each implementation should handle ~122k records efficiently
- Focus on response time and throughput metrics
- Use separate machines for API server and load generator
- **Comprehensive testing**: Use `postal_api_test_suite.py` for standardized performance and functionality validation

## Data Mapping
CSV columns → API fields:
- PNA → postal_code
- Miejscowość → city  
- Ulica → street
- Numery → house_numbers
- Gmina → municipality
- Powiat → county
- Województwo → province