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

### Flask Implementation Details
- **Database**: SQLite with full indexing on searchable fields
- **Search Strategy**: Partial city matching, exact street/other fields, case-insensitive
- **API Pattern**: RESTful with hierarchical location endpoints
- **Performance**: Optimized with database indexes for all query fields
- **Fallback Logic**: Cascading search fallbacks (house_number → street → city-only)
- **Production Server**: Gunicorn with multiple workers
- **Code Architecture**: Refactored with reusable query builder functions

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
cd flask

# Create/recreate database from CSV
python create_db.py

# Development server (localhost:5001)  
python app.py

# Production server (recommended for testing)
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5001 app:app

# Test API
curl "http://localhost:5001/health"
curl "http://localhost:5001/postal-codes?city=Warszawa&street=Jodłowa"
curl "http://localhost:5001/locations/provinces"
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
- **house_number**: Matches against exact "Numery" field values
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
- Indexing strategy is critical for query performance
- Each implementation should handle ~117k records efficiently
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