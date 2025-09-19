# Go Postal Code API

This is a Go implementation of the Polish postal code API, providing all the same functionality as the Flask and FastAPI versions.

## Features

- **Complete API compatibility** with Flask/FastAPI implementations
- **High-performance Gin web framework** for production workloads
- **Full Polish character normalization** with fallback search
- **Sophisticated house number matching** supporting Polish addressing patterns
- **Built-in production server** (no external server required)
- **Comprehensive location hierarchy** endpoints
- **Intelligent fallback logic** for enhanced user experience

## Architecture

```
go/
├── main.go                           # Application entry point and server setup
├── internal/
│   ├── database/
│   │   └── database.go              # SQLite database connection and models
│   ├── utils/
│   │   ├── polish_normalizer.go     # Polish character normalization
│   │   └── house_number_matcher.go  # Polish address pattern matching
│   ├── services/
│   │   └── postal_service.go        # Core business logic and search
│   └── routes/
│       └── routes.go                # HTTP API routes and handlers
├── test_basic.go                     # Basic API validation tests
└── simple_debug.go                   # Direct service layer testing
```

## Quick Start

### Prerequisites
- Go 1.19+ installed
- Database file `postal_codes.db` in parent directory (run `python create_db.py` from project root)

### Development Server
```bash
cd go
go mod tidy
go run main.go
```
Server starts on `http://localhost:5003`

### Production Build
```bash
cd go
go build -o postal-api main.go
./postal-api
```

## API Endpoints

### Core Search
- `GET /postal-codes?city=X&street=Y&house_number=Z&limit=N` - Multi-parameter search
- `GET /postal-codes/{code}` - Direct postal code lookup

### Location Hierarchy
- `GET /locations` - Available endpoints directory
- `GET /locations/provinces?prefix=X` - All provinces, optionally filtered
- `GET /locations/counties?province=X&prefix=Y` - Counties, optionally filtered
- `GET /locations/municipalities?province=X&county=Y&prefix=Z` - Municipalities
- `GET /locations/cities?province=X&county=Y&municipality=Z&prefix=W` - Cities
- `GET /locations/streets?city=X&prefix=Y` - Streets in a city

### System
- `GET /health` - Health check endpoint

## Testing

### Basic Tests
```bash
go run test_basic.go
```

### Service Layer Tests
```bash
go run simple_debug.go
```

### Manual API Tests
```bash
# Health check
curl "http://localhost:5003/health"

# Search postal codes
curl "http://localhost:5003/postal-codes?city=Warszawa&limit=3"

# House number matching (Polish patterns)
curl "http://localhost:5003/postal-codes?city=Warszawa&street=Edwarda%20Józefa%20Abramowskiego&house_number=5"

# Direct postal code lookup
curl "http://localhost:5003/postal-codes/01-497"

# Location hierarchy
curl "http://localhost:5003/locations/provinces"
```

## Performance Notes

- **Built-in production server**: Go's HTTP server is production-ready out of the box
- **Efficient pattern matching**: House number ranges processed at ~0.01ms per evaluation
- **Database optimizations**: Full indexing on searchable fields
- **Memory efficient**: Pointer types for nullable database fields
- **Concurrent safe**: All handlers are goroutine-safe

## Polish Feature Support

### Character Normalization
- Automatic fallback to ASCII equivalents: `ą→a, ć→c, ę→e, ł→l, ń→n, ó→o, ś→s, ź→z, ż→z`
- Case-insensitive matching
- Prefix-based autocomplete support

### House Number Patterns
- Simple ranges: `"1-12"`
- Side indicators: `"1-41(n)"` (odd), `"2-38(p)"` (even)
- Open-ended: `"337-DK"` (do końca/to end)
- Letter suffixes: `"4a-9/11"`, `"31-31a"`
- Slash notation: `"55-69/71(n)"`, `"2/4"`
- Individual numbers: `"60"`, `"35c"`

### Intelligent Fallbacks
1. **Exact match** → Perfect result
2. **Polish normalization** → Character-normalized search
3. **House number fallback** → Remove invalid house number
4. **Street fallback** → Remove invalid street, return city results
5. **Polish fallbacks** → Apply normalization to fallback searches

## Development

The Go implementation mirrors the Flask architecture while leveraging Go's strengths:
- **Type safety** with compile-time error checking
- **Performance** with native concurrency
- **Simplicity** with minimal external dependencies
- **Production readiness** with built-in HTTP server

All functionality from the Flask/FastAPI versions has been preserved and optimized for Go's ecosystem.