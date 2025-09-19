# Elixir Postal Code API Implementation

High-performance Elixir implementation of the Polish Postal Code API, designed for concurrent request handling and fault tolerance.

## Key Features

- **Concurrent Processing**: Built on the Actor model with OTP (Open Telecom Platform)
- **Fault Tolerance**: Supervisor trees ensure system resilience
- **High Performance**: Compiled BEAM bytecode with efficient pattern matching
- **Identical Functionality**: Same four-tier search strategy as Flask/FastAPI/Go implementations
- **Port 5004**: Dedicated port for performance comparison testing

## Architecture

### OTP Application Structure
```
PostalCodeApi.Application (Supervisor)
├── PostalCodeApi.Database (GenServer) - Database connection manager
└── Plug.Cowboy (HTTP Server) - Handles HTTP requests
```

### Module Organization
```
lib/postal_code_api/
├── application.ex          # OTP application entry point
├── database.ex            # Database connection GenServer
├── router.ex              # HTTP routing with Plug
├── postal_service.ex      # Core search logic (four-tier strategy)
├── house_number_matcher.ex # Pattern matching engine
└── polish_normalizer.ex   # Character normalization
```

## Quick Start

### Prerequisites
- Elixir 1.14+ and Erlang/OTP 25+
- SQLite database at `../postal_codes.db` (run `python create_db.py` from project root)

### Installation
```bash
cd elixir

# Install dependencies
mix deps.get

# Compile the application
mix compile
```

### Development Server
```bash
# Start the application
mix run --no-halt

# Server will start on http://localhost:5004
```

### Production Deployment
```bash
# Create a release
mix release

# Run the release
_build/prod/rel/postal_code_api/bin/postal_code_api start
```

## API Endpoints

### Core Search Endpoints
All endpoints match the Flask/FastAPI/Go implementations:

**Multi-Parameter Search**:
```
GET /postal-codes?city=Warszawa&street=Abramowskiego&house_number=5
```

**Direct Code Lookup**:
```
GET /postal-codes/02-659
```

### Location Hierarchy Endpoints
**Discovery**: `GET /locations`

**Hierarchical Filtering**:
- `GET /locations/provinces?prefix=X`
- `GET /locations/counties?province=X&prefix=Y`
- `GET /locations/municipalities?province=X&county=Y&prefix=Z`
- `GET /locations/cities?province=X&county=Y&municipality=Z&prefix=W`

**Street Discovery**:
- `GET /locations/streets?city=X&prefix=Y`

### Health Check
**Monitoring**: `GET /health`

## Testing

### Unit Tests
```bash
# Run all tests
mix test

# Run with detailed output
mix test --trace
```

### Manual API Testing
```bash
# Test health endpoint
curl http://localhost:5004/health

# Test postal code search
curl "http://localhost:5004/postal-codes?city=Warszawa"

# Test direct lookup
curl http://localhost:5004/postal-codes/02-659
```

### Comprehensive Testing
```bash
# From project root, test all APIs including Elixir
python3 comprehensive_postal_test_suite.py --port 5004
```

## Four-Tier Search Strategy

The Elixir implementation maintains identical search logic to other implementations:

### Tier 1: Exact Search
- Uses original user input parameters
- SQL pre-filtering + Elixir pattern matching for house numbers

### Tier 2: Polish Character Normalization
- Converts input to ASCII equivalents using `PolishNormalizer`
- Searches against `_normalized` database columns

### Tier 3: Intelligent Fallbacks
- House Number Fallback: Remove invalid house number
- Street Fallback: Remove invalid street
- Clear messaging about what was found instead

### Tier 4: Polish Normalization Fallbacks
- Applies fallback logic to normalized parameters
- Final attempt using ASCII-converted search terms

## Performance Characteristics

### Elixir-Specific Optimizations

**Concurrent Request Handling**:
- BEAM VM scheduler efficiently manages thousands of lightweight processes
- Each request handled in its own process for isolation

**Pattern Matching Performance**:
- Native Elixir pattern matching for house number ranges
- Compiled guards for even/odd number checking

**Memory Management**:
- Garbage collection per process, not global
- Efficient binary handling for string operations

**Database Connection**:
- GenServer-managed connection pooling
- Fault tolerance with automatic restart

### Benchmarking Standards

For fair performance comparison with other implementations:

```bash
# Start production-ready server
mix run --no-halt
```

Server runs on port 5004 with:
- Cowboy HTTP server (production-grade)
- Compiled BEAM bytecode
- OTP supervision for reliability

## Code Quality & Patterns

### Elixir Conventions
- **Pattern Matching**: Extensive use for control flow and data extraction
- **Pipe Operator**: Functional data transformation pipelines
- **Guards**: Compile-time optimizations for type checking
- **GenServer**: Stateful database connection management
- **Supervisor Trees**: Fault tolerance and system resilience

### Error Handling
- **Let It Crash**: Elixir philosophy for error recovery
- **Supervisor Restart**: Automatic process restart on failure
- **Pattern Matching**: Explicit error case handling
- **Graceful Degradation**: Meaningful responses for edge cases

### Functional Programming
- **Immutable Data**: No mutable state, preventing race conditions
- **Pure Functions**: Side-effect-free business logic
- **Higher-Order Functions**: Enum operations for data processing
- **Recursive Algorithms**: Tail-recursive list processing

## Development Guidelines

### Adding Features
1. **Maintain Consistency**: Mirror changes across all implementations
2. **Follow OTP Principles**: Use GenServers for stateful components
3. **Pattern Match Everything**: Leverage Elixir's strengths
4. **Test Comprehensively**: Unit tests + integration tests

### Performance Tuning
1. **Profile with :observer**: Visual process monitoring
2. **Benchmark Critical Paths**: House number matching performance
3. **Monitor Memory Usage**: Per-process garbage collection
4. **Test Under Load**: Concurrent request handling

### Debugging
1. **IEx Integration**: Interactive debugging console
2. **Process Inspection**: Monitor GenServer state
3. **Distributed Tracing**: Follow request paths
4. **Supervisor Logs**: System restart and error information

## Production Considerations

### Deployment
- **Release Building**: `mix release` for production deployments
- **Configuration**: Environment-specific config files
- **Monitoring**: Built-in health checks and metrics
- **Logging**: Structured logging with metadata

### Scaling
- **Horizontal Scaling**: Multiple BEAM nodes
- **Load Balancing**: Distribute across instances
- **Database Pooling**: Connection management
- **Process Limits**: Configure maximum process counts

### Monitoring
- **Health Endpoints**: `/health` for load balancer checks
- **Metrics Collection**: Response time and throughput
- **Error Tracking**: Comprehensive error logging
- **Performance Monitoring**: Built-in BEAM metrics

---

This Elixir implementation demonstrates the language's strengths in building concurrent, fault-tolerant systems while maintaining complete API compatibility with other technology implementations.