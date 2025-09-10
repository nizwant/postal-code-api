# Flask Postal Code API

A REST API for Polish postal code lookups built with Flask and SQLite.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create the database:
```bash
python create_db.py
```

3. Run the server:
```bash
python app.py
```

Server runs on http://localhost:5001

## API Endpoints

### Search Postal Codes
`GET /postal-codes`

Query parameters:
- `city` - City name (exact match, case-insensitive)
- `street` - Street name (exact match, case-insensitive)
- `house_number` - House number (exact match)
- `province` - Province/Województwo (exact match, case-insensitive)
- `county` - County/Powiat (exact match, case-insensitive)
- `municipality` - Municipality/Gmina (exact match, case-insensitive)
- `limit` - Maximum results (default: 100)

Example:
```bash
curl "http://localhost:5001/postal-codes?city=Abramy&limit=5"
```

### Get Specific Postal Code
`GET /postal-codes/{postal_code}`

Example:
```bash
curl "http://localhost:5001/postal-codes/03-506"
```

### Get Available Location Endpoints
`GET /locations`

Returns available location endpoints.

Example:
```bash
curl "http://localhost:5001/locations"
```

### Get Provinces
`GET /locations/provinces`

Returns all available provinces.

Example:
```bash
curl "http://localhost:5001/locations/provinces"
```

### Get Counties
`GET /locations/counties`

Query parameters:
- `province` - Filter counties by province

Examples:
```bash
curl "http://localhost:5001/locations/counties"
curl "http://localhost:5001/locations/counties?province=mazowieckie"
```

### Get Municipalities
`GET /locations/municipalities`

Query parameters:
- `province` - Filter by province
- `county` - Filter by county

Examples:
```bash
curl "http://localhost:5001/locations/municipalities"
curl "http://localhost:5001/locations/municipalities?province=mazowieckie&county=Warszawa"
```

### Get Cities
`GET /locations/cities`

Query parameters:
- `province` - Filter by province
- `county` - Filter by county
- `municipality` - Filter by municipality

Examples:
```bash
curl "http://localhost:5001/locations/cities"
curl "http://localhost:5001/locations/cities?province=mazowieckie&county=Warszawa"
```

### Health Check
`GET /health`

Example:
```bash
curl "http://localhost:5001/health"
```

## Database

- **Engine**: SQLite
- **Records**: ~117k Polish postal codes
- **Indexes**: Created on all searchable fields for performance