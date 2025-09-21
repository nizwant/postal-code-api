# CLAUDE.md - Comprehensive Polish Postal Code API Project Guide

This file provides definitive guidance to Claude Code (claude.ai/code) when working with this sophisticated multi-technology postal code API project.

## 🎯 Project Mission

This is a **multi-technology API performance comparison framework** for Polish postal code lookups, designed to solve real-world address lookup challenges while comparing performance across different technologies and frameworks.

### Core Philosophy: Postal Code Delivery Over Input Validation

**Primary Goal**: Return a useful postal code for any reasonable address query. We prioritize **usefulness over strictness**.

The API exists to help humans find postal codes, not to validate input perfection. This means:
- Intelligent fallbacks instead of strict failures
- Polish character normalization for accessibility
- Graceful handling of incomplete or imperfect address data
- Real human behavior simulation in testing

## 🏗️ Data Architecture

### Source Data Transformation
- **Original**: `postal_codes_poland.csv` (7.1MB, 117,679 records)
- **Normalized**: `postal_codes.db` (31MB, 122,765 records)
- **Growth**: 1.04x expansion due to house number range normalization

### Database Schema
```sql
CREATE TABLE postal_codes (
    id INTEGER PRIMARY KEY,
    postal_code TEXT NOT NULL,
    city TEXT,
    city_normalized TEXT,         -- ASCII equivalent for search
    street TEXT,
    street_normalized TEXT,       -- ASCII equivalent for search
    house_numbers TEXT,           -- Single range pattern (normalized)
    municipality TEXT,
    county TEXT,
    province TEXT
);
```

### Key Normalization Process (`create_db.py`)
1. **House Number Range Splitting**: `"270-336(p), 283-335(n)"` → separate records for `"270-336(p)"` and `"283-335(n)"`
2. **Polish Character Normalization**: `"Łódź"` → `"Lodz"` in `_normalized` columns
3. **Full Indexing**: All searchable fields indexed for performance
4. **Performance Result**: 0.01ms per house number pattern evaluation

## 🔍 Core Search Engine - Four-Tier Strategy

The search engine implements a sophisticated four-tier approach with intelligent fallbacks:

### Tier 1: Exact Search
- Uses original user input parameters
- SQL pre-filtering + Python pattern matching for house numbers
- Handles exact matches without character normalization

### Tier 2: Polish Character Normalization
- Converts input to ASCII equivalents (`"Łódź"` → `"Lodz"`)
- Searches against `_normalized` database columns
- Enables accessibility for users without Polish keyboard

### Tier 3: Intelligent Fallbacks (Original Parameters)
When no results found, cascading fallback logic:
1. **House Number Fallback**: Remove invalid house number, return street-level results
2. **Street Fallback**: Remove invalid street, return city-level results
3. **Graceful Messaging**: Clear explanations of what was found instead

### Tier 4: Polish Normalization Fallbacks
- Applies same fallback logic to normalized parameters
- Final attempt using ASCII-converted search terms
- Catches cases where Polish characters caused the initial search to fail

### Implementation (`postal_service.py:search_postal_codes`)
```python
# Tier 1: Exact search
exact_results = filter_by_house_number(sql_results, house_number, limit)

if not exact_results:
    # Tier 2: Polish normalization
    polish_results = search_with_normalized_params(...)

    if not polish_results:
        # Tier 3: Fallback logic (original)
        results, fallback_used, message = search_with_fallbacks(...)

        if not results:
            # Tier 4: Polish normalization + fallbacks
            results = search_with_fallbacks(..., use_normalized=True)
```

## 🏠 House Number Pattern Matching Engine

### Supported Polish Addressing Patterns (`house_number_matcher.py`)

**Simple Ranges**: `"1-12"`
**Side Indicators**:
- `"1-41(n)"` - nieparzyste (odd numbers only)
- `"2-38(p)"` - parzyste (even numbers only)

**Open-Ended Ranges**:
- `"337-DK"` - do końca (to infinity)
- `"2-DK(p)"` - infinite even numbers from 2

**Letter Suffixes**: `"4a-9/11"`, `"31-31a"`, `"22-22b"`

**Complex Slash Notation**:
- `"1/3-23/25(n)"` - individual numbers: 1, 3, 23, 25 (odd only)
- `"55-69/71(n)"` - range 55-69 plus 71 (odd only)
- `"2/4-10(p)"` - range 4-10 (even only)

**Individual Numbers**: `"60"`, `"35c"`

### Pattern Matching Strategy
- **SQL Pre-filtering**: City/street/location filtering with database indexes
- **Python Pattern Matching**: Complex house number evaluation (0.01ms per record)
- **Hybrid Performance**: Optimal balance of database efficiency and pattern flexibility

## 🌐 Multi-Technology Implementation Architecture

### Flask Implementation (`flask/`)
**Mature, Complete Reference Implementation**
```
flask/
├── app.py                    # Flask app bootstrap + DB validation
├── routes.py                 # API endpoint definitions
├── postal_service.py         # Core search logic (shared)
├── house_number_matcher.py   # Pattern matching engine (shared)
├── polish_normalizer.py      # Character normalization (shared)
├── database.py              # DB connection utilities (shared)
├── tests/                   # Comprehensive test suite
└── run_tests.py             # Test runner with detailed output
```

**Key Features**:
- Modular architecture with clear separation of concerns
- Comprehensive test coverage
- Production-ready with Gunicorn deployment
- Reference implementation for other technologies

### FastAPI Implementation (`fastapi/`)
**High-Performance with Automatic Documentation**
```
fastapi/
├── main.py                  # FastAPI app with startup validation
├── app.py                   # Gunicorn entry point
├── routes.py                # FastAPI router with type hints
├── postal_service.py        # Shared core logic (identical to Flask)
├── house_number_matcher.py  # Shared pattern engine
├── polish_normalizer.py     # Shared normalization
├── database.py             # Shared DB utilities
└── test_basic.py           # Basic API validation
```

**Key Features**:
- Automatic OpenAPI documentation generation
- Type validation with Pydantic
- Async-ready architecture
- Performance-optimized with Uvicorn workers

### Go Implementation (`go/`)
**High-Performance Concurrent Implementation**
```
go/
├── main.go                  # Server bootstrap
├── internal/
│   ├── database/           # DB connection management
│   ├── routes/             # HTTP route handlers
│   ├── services/           # Business logic layer
│   └── utils/              # Shared utilities
├── README.md               # Go-specific documentation
└── test_basic.go          # Basic validation tests
```

**Key Features**:
- Built-in production HTTP server
- Concurrent request handling
- Compiled binary deployment
- Memory-efficient processing

### Elixir Implementation (`elixir/`)
**High-Performance Concurrent Implementation with OTP**
```
elixir/
├── lib/postal_code_api/
│   ├── application.ex          # OTP application entry point
│   ├── database.ex            # Database connection GenServer
│   ├── router.ex              # HTTP routing with Plug
│   ├── postal_service.ex      # Core search logic (four-tier strategy)
│   ├── house_number_matcher.ex # Pattern matching engine
│   └── polish_normalizer.ex   # Character normalization
├── mix.exs                    # Project configuration
├── README.md                  # Elixir-specific documentation
└── test/                     # Unit tests
```

**Key Features**:
- Actor model with OTP supervision trees
- Fault tolerance and automatic restart
- BEAM VM concurrent processing
- Functional programming paradigms
- Pattern matching optimization

### Frontend Implementation (`frontend/`)
**Next.js + TypeScript User Interface**
```
frontend/
├── src/
│   ├── app/                # Next.js app router
│   ├── components/         # Reusable UI components
│   └── lib/               # Utility functions
├── package.json           # Dependencies
└── tailwind.config.js     # Styling configuration
```

**Key Features**:
- TypeScript for type safety
- Tailwind CSS for rapid styling
- Component-based architecture
- API integration with multiple backends

## 🧪 Testing Philosophy & Infrastructure

### Core Testing Principle
**"Would a human get a useful postal code?"**

Every test validates whether the API provides helpful results for real-world queries, not whether it strictly validates input.

### Test Categories (`comprehensive_postal_test_suite.py`)

**CORE Tests** - Must pass (pipeline integrity):
- Exact address matches
- Database consistency validation
- Basic API functionality

**HUMAN Tests** - May fail (real user behavior simulation):
- Typos and misspellings
- Wrong street in correct city
- Partial address information
- Case and spacing variations

**EDGE Tests** - Should handle gracefully:
- Boundary conditions
- Malformed input
- Empty parameters

**PERFORMANCE Tests** - Benchmarking standards:
- Response time measurements
- Throughput testing
- Cross-API consistency

### Fallback Expectations
```python
# Test validation patterns
{
    "query": "Wrong street in Kraków",
    "fallback_expected": True,
    "expected_city": "Kraków",           # Should fallback to city
    "message_contains": "Street not found"
}

{
    "query": "House 500 on street with range 1-19",
    "fallback_expected": True,
    "expected_street_contains": "target_street",  # Should fallback to street
    "message_contains": "House number not found"
}
```

### Test Suite Usage
```bash
# Test all APIs (comprehensive)
python3 comprehensive_postal_test_suite.py

# Test specific implementation
python3 comprehensive_postal_test_suite.py --api flask
python3 comprehensive_postal_test_suite.py --port 5003  # Go implementation
python3 comprehensive_postal_test_suite.py --port 5004  # Elixir implementation

# Targeted test runs
python3 comprehensive_postal_test_suite.py --core-tests      # Essential functionality
python3 comprehensive_postal_test_suite.py --human-tests    # User behavior simulation
python3 comprehensive_postal_test_suite.py --polish-tests   # Character normalization
python3 comprehensive_postal_test_suite.py --save-results   # Export detailed JSON
```

## 🚀 Development Workflows

### Project Setup (One-time)
```bash
# Install dependencies
poetry install

# Create normalized database (run once from project root)
python create_db.py
```

### Flask Development (Port 5001)
```bash
cd flask

# Development server
python app.py

# Production server (recommended for testing)
pip install gunicorn
gunicorn --workers 4 --bind 0.0.0.0:5001 app:app

# Run comprehensive tests
python run_tests.py
```

### FastAPI Development (Port 5002)
```bash
cd fastapi

# Development server
python main.py

# Production server (recommended)
pip install uvicorn[standard] gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5002

# View automatic documentation
curl "http://localhost:5002/docs"

# Run basic tests
python test_basic.py
```

### Go Development (Port 5003)
```bash
cd go

# Development/Production (same binary)
go build -o postal-api main.go
./postal-api

# Run tests
go test ./...
```

### Elixir Development (Port 5004)
```bash
cd elixir

# Install dependencies
mix deps.get

# Development server
mix run --no-halt

# Production release
mix release
_build/prod/rel/postal_code_api/bin/postal_code_api start

# Run tests
mix test
```

### Frontend Development (Port 3000)
```bash
cd frontend

# Development server
npm run dev

# Production build
npm run build
npm start
```

## 📋 API Design Standards

### Core Search Endpoints
All implementations must provide consistent endpoints:

**Multi-Parameter Search**:
```
GET /postal-codes?city=Warszawa&street=Abramowskiego&house_number=5
```

**Direct Code Lookup**:
```
GET /postal-codes/02-659
```

### Location Hierarchy Endpoints
**Discovery**: `GET /locations` - Available endpoints directory

**Hierarchical Filtering**:
- `GET /locations/provinces?prefix=X`
- `GET /locations/counties?province=X&prefix=Y`
- `GET /locations/municipalities?province=X&county=Y&prefix=Z`
- `GET /locations/cities?province=X&county=Y&municipality=Z&prefix=W`

**Street Discovery**:
- `GET /locations/streets?city=X&prefix=Y`

### Response Format Standards

**Successful Search**:
```json
{
  "results": [
    {
      "postal_code": "02-659",
      "city": "Warszawa",
      "street": "Edwarda Józefa Abramowskiego",
      "house_numbers": "1-19(n)",
      "municipality": "Warszawa",
      "county": "Warszawa",
      "province": "Mazowieckie"
    }
  ],
  "count": 1,
  "search_type": "exact"
}
```

**Fallback Response**:
```json
{
  "results": [...],
  "count": 5,
  "search_type": "exact",
  "fallback_used": true,
  "message": "House number '500' not found on street 'Abramowskiego' in city 'Warszawa'. Showing all results for street 'Abramowskiego' in 'Warszawa'."
}
```

**Polish Normalization**:
```json
{
  "results": [...],
  "count": 3,
  "search_type": "polish_characters",
  "polish_normalization_used": true,
  "message": "Search performed with Polish character normalization."
}
```

### Search Behavior Requirements

**City Matching**: Partial matching - `"Warszawa"` matches `"Warszawa (Mokotów)"`

**Street Matching**: Partial matching - `"Główna"` matches `"ul. Główna"`

**House Number Matching**: Complex pattern evaluation using `house_number_matcher.py`

**Other Fields**: Exact matching, case-insensitive

**Polish Characters**: Full support via URL encoding + normalized search columns

**Fallback Priority**:
1. Remove invalid house_number → return street-level results
2. Remove invalid street → return city-level results
3. Graceful failure only for severe input errors

**Result Limiting**: `limit` parameter (default 100, minimum 1)

## ⚡ Performance Optimization Guidelines

### Database Performance
- **Indexes**: All searchable fields fully indexed
- **Normalization**: Pre-computed ASCII columns avoid runtime conversion
- **Connection Management**: Efficient connection pooling per technology

### Search Strategy Performance
- **SQL Pre-filtering**: Reduce dataset before Python pattern matching
- **Pattern Matching**: 0.01ms per evaluation, batched processing
- **Memory Usage**: Streaming results, limited result sets

### Technology-Specific Optimizations

**Flask**:
- Gunicorn with multiple workers
- Connection pooling for SQLite
- Efficient fallback query reuse

**FastAPI**:
- Uvicorn workers for async performance
- Pydantic validation caching
- Type hint optimizations

**Go**:
- Goroutine concurrency
- Compiled binary efficiency
- Built-in HTTP server performance

**Elixir**:
- Actor model with lightweight processes
- OTP supervision for fault tolerance
- BEAM VM pattern matching optimization
- Functional programming efficiency

## 🛠️ Code Architecture Patterns

### Shared Components
These components should be identical across implementations:
- **House Number Matching Logic**: Core algorithm consistency
- **Polish Character Normalization**: Identical character mapping
- **Fallback Message Templates**: Consistent user experience
- **Database Schema**: Identical table structure and indexes

### Technology-Specific Patterns

**Modular Architecture** (Flask/FastAPI):
```
routes.py          → API endpoint definitions
postal_service.py  → Core business logic
house_number_matcher.py → Pattern matching engine
polish_normalizer.py    → Character normalization
database.py        → Connection management
```

**Package Architecture** (Go):
```
internal/routes/    → HTTP handlers
internal/services/  → Business logic
internal/database/  → Data access layer
internal/utils/     → Shared utilities
```

**OTP Architecture** (Elixir):
```
lib/postal_code_api/
├── application.ex          → OTP supervision tree
├── database.ex            → GenServer for DB connection
├── router.ex              → Plug HTTP routing
├── postal_service.ex      → Core business logic
├── house_number_matcher.ex → Pattern matching
└── polish_normalizer.ex   → Character normalization
```

### Error Handling Standards
- **Database Errors**: Graceful degradation with clear messages
- **Validation Errors**: Helpful guidance, not strict rejection
- **Performance Errors**: Timeout handling with partial results
- **Fallback Messaging**: Clear explanation of what was found instead

## 📊 Production Deployment Standards

### Performance Comparison Requirements
For fair benchmarking, each technology must use production-grade servers:

**Flask** (Port 5001):
```bash
gunicorn --workers 4 --bind 0.0.0.0:5001 app:app
```

**FastAPI** (Port 5002):
```bash
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5002
```

**Go** (Port 5003):
```bash
go build -o postal-api main.go
./postal-api  # Built-in production server
```

**Elixir** (Port 5004):
```bash
mix run --no-halt  # Development/Production server
```

### Monitoring & Health Checks
All implementations must provide:
- `GET /health` endpoint for monitoring
- Consistent response time logging
- Error rate tracking
- Database connection validation

### Deployment Validation
Before benchmarking:
1. Run `comprehensive_postal_test_suite.py` for functionality validation
2. Verify database normalization with `create_db.py`
3. Test fallback logic with known edge cases
4. Validate Polish character handling

## 💡 Development Guidelines for Claude

### When Adding Features
1. **Consistency First**: Implement in reference Flask version first
2. **Mirror Across Technologies**: Maintain identical core logic
3. **Test Thoroughly**: Use comprehensive test suite for validation
4. **Document Changes**: Update this CLAUDE.md file

### When Debugging Issues
1. **Check Fallback Logic**: Most issues are in the four-tier search strategy
2. **Validate House Number Patterns**: Complex regex patterns in `house_number_matcher.py`
3. **Test Polish Characters**: Normalization issues are common
4. **Cross-Reference Implementations**: Compare Flask vs FastAPI vs Go vs Elixir

### When Optimizing Performance
1. **Profile SQL Queries**: Check index usage and query plans
2. **Measure Pattern Matching**: Time house number evaluations
3. **Test Concurrency**: Validate under load with multiple technologies
4. **Monitor Memory Usage**: Especially important for large result sets

### Code Quality Standards
- **NEVER add comments unless explicitly requested**
- **Follow existing patterns** in each technology implementation
- **Maintain shared component consistency** across Flask/FastAPI/Go/Elixir
- **Prioritize performance** while maintaining accuracy
- **Test fallback scenarios** thoroughly
- **Handle Polish characters** gracefully in all contexts

---

This documentation serves as the definitive guide for understanding and extending this sophisticated postal code API project. When in doubt, refer to the Flask implementation as the reference standard and maintain consistency across all technologies.