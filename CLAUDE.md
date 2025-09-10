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
- **Search Strategy**: Exact matching, case-insensitive
- **API Pattern**: RESTful with hierarchical location endpoints
- **Performance**: Optimized with database indexes for all query fields

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

# Run Flask server (localhost:5001)  
python app.py

# Test API
curl "http://localhost:5001/health"
curl "http://localhost:5001/postal-codes?city=Abramy"
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
- Exact matching only (no partial/fuzzy search)
- Case-insensitive for text fields
- house_number matches against exact "Numery" field values
- Results limited by `limit` parameter (default 100)

## Performance Considerations

The goal is API performance comparison, so:
- Database choice should optimize for read performance
- Indexing strategy is critical for query performance
- Each implementation should handle ~117k records efficiently
- Focus on response time and throughput metrics

## Data Mapping
CSV columns → API fields:
- PNA → postal_code
- Miejscowość → city  
- Ulica → street
- Numery → house_numbers
- Gmina → municipality
- Powiat → county
- Województwo → province