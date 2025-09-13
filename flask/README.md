# Flask Postal Code API

A REST API for Polish postal code lookups with sophisticated house number pattern matching.

## Features

- **Full Address Lookup**: Find exact postal codes using complete addresses
- **Smart House Number Matching**: Handles complex Polish addressing patterns:
  - Simple ranges: `"1-12"`
  - Side indicators: `"1-41(n)"` (odd), `"2-38(p)"` (even)
  - Open-ended ranges: `"337-DK"` (to infinity)
  - Letter suffixes: `"4a-9/11"`, `"31-31a"`
  - Complex patterns: `"1/3-23/25(n)"`
- **Intelligent Fallbacks**: Graceful degradation when exact matches aren't found
- **Location Hierarchy**: Browse provinces, counties, municipalities, and cities

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create the normalized database:
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
- `city` - City name (partial match, case-insensitive)
- `street` - Street name (exact match, case-insensitive)
- `house_number` - **House number with smart pattern matching**
- `province` - Province/Województwo (exact match, case-insensitive)
- `county` - County/Powiat (exact match, case-insensitive)
- `municipality` - Municipality/Gmina (exact match, case-insensitive)
- `limit` - Maximum results (default: 100)

**Full Address Lookup Examples:**
```bash
# Find exact postal code for house number 5 on Abramowskiego street in Warszawa
curl "http://localhost:5001/postal-codes?city=Warszawa&street=Edwarda%20Józefa%20Abramowskiego&house_number=5"
# Returns: 02-659 (matches range "1-19(n)" for odd numbers)

# Find postal code for even house number
curl "http://localhost:5001/postal-codes?city=Warszawa&street=Edwarda%20Józefa%20Abramowskiego&house_number=6"
# Returns: 02-659 (matches range "2-16a(p)" for even numbers)

# Basic city search
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