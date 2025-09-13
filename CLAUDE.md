# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a multi-technology API performance comparison project for Polish postal code lookups. The project contains separate implementations in different frameworks/languages (Flask, FastAPI, Elixir, Go) to compare performance across technologies.

## Architecture

### Data Source
- **Source**: `postal_codes_poland.csv` (~7.5MB, 117k records) 
- **Schema**: PNA (postal code), Miejscowość (city), Ulica (street), Numery (house numbers), Gmina (municipality), Powiat (county), Województwo (province)

### Implementation Structure
Each technology implementation is in its own directory:
- `flask/` - Flask + SQLite implementation (currently complete)
- `fastapi/` - FastAPI implementation (placeholder)
- `elixir/` - Elixir implementation (placeholder)
- `go/` - Go implementation (placeholder)

### Shared Database
- **Database**: `postal_codes.db` (25MB, 122k normalized records) in project root
- **Creation Script**: `create_db.py` in project root - run once for all implementations
- **CSV Source**: `postal_codes_poland.csv` (7.5MB original data) in project root

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
  - `app.py` - Flask API endpoints and search orchestration
  - `house_number_matcher.py` - Dedicated pattern matching engine
  - `../create_db.py` - Database normalization and creation (project root)
  - `tests/` - Comprehensive test suite with API and unit tests

## Common Development Commands

### Project Setup
```bash
# Install dependencies (Poetry managed)
poetry install

# For Flask specifically
cd flask
pip install -r requirements.txt
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
- `GET /locations/provinces` - All provinces
- `GET /locations/counties?province=X` - Counties, optionally filtered
- `GET /locations/municipalities?province=X&county=Y` - Municipalities, optionally filtered  
- `GET /locations/cities?province=X&county=Y&municipality=Z` - Cities, optionally filtered

### Search Behavior Requirements
- **City matching**: Partial matching (e.g., "Warszawa" matches "Warszawa (Mokotów)")
- **Other fields**: Exact matching, case-insensitive
- **house_number**: **ENHANCED** - Sophisticated pattern matching against normalized ranges:
  - Handles Polish addressing patterns: `"1-19(n)"`, `"2-38(p)"`, `"337-DK"`, `"4a-9/11"`
  - Uses dedicated pattern matching engine (`house_number_matcher.py`)
  - Performance: 0.01ms per pattern evaluation
- **Fallback logic**: Cascading fallbacks when no results found:
  1. Remove house_number parameter if present
  2. Remove street parameter if still no results
- **Results**: Limited by `limit` parameter (default 100)
- **Polish characters**: Supported via URL encoding

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

## Data Mapping
CSV columns → API fields:
- PNA → postal_code
- Miejscowość → city  
- Ulica → street
- Numery → house_numbers
- Gmina → municipality
- Powiat → county
- Województwo → province