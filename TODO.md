# Postal Code API Performance Comparison - TODO

## Infrastructure Setup

### 1. Set up Ubuntu server as dedicated API server machine
- [ ] Choose which Ubuntu server to use as API host
- [ ] Configure server environment (Python, Go, Elixir runtimes)
- [ ] Set up database storage and optimization
- [ ] Configure network settings for external access
- [ ] Install monitoring tools (htop, iostat, etc.)

### 2. Deploy Flask API to Ubuntu server
- [ ] Transfer Flask code and CSV data to server
- [ ] Install Python dependencies (Flask, pandas, sqlite3)
- [ ] Create database using `create_db.py`
- [ ] Configure Flask to run on external interface (0.0.0.0)
- [ ] Test API accessibility from other machines
- [ ] Set up process management (systemd service or similar)

### 3. Set up second machine as load generator
- [ ] Choose load generator machine (Ubuntu server or PC)
- [ ] Ensure network connectivity to API server
- [ ] Install required tools and dependencies
- [ ] Configure network settings for optimal testing

### 4. Install performance testing tools (wrk, hey, or locust)
- [ ] Install wrk: `sudo apt install wrk` or build from source
- [ ] Install hey: Download from GitHub releases
- [ ] Install locust: `pip install locust` (if using Python-based testing)
- [ ] Test basic connectivity with simple HTTP requests

## Development

### 5. Create standardized test suite for API comparison
- [ ] Define common test scenarios (simple search, complex filters, etc.)
- [ ] Create test data sets with realistic query patterns
- [ ] Design metrics collection (response time, throughput, errors)
- [ ] Write test scripts that can run against any API implementation
- [ ] Document test methodology and expected outputs

### 6. Implement FastAPI version of postal code API
- [ ] Create `fastapi/` directory structure
- [ ] Implement same database schema and indexing strategy
- [ ] Create identical API endpoints to Flask version
- [ ] Add FastAPI-specific optimizations (async, Pydantic models)
- [ ] Test API compatibility with existing test suite

### 7. Implement Go version of postal code API
- [ ] Create `go/` directory with proper module structure
- [ ] Choose Go database library (database/sql + sqlite3 driver)
- [ ] Implement HTTP router and handlers
- [ ] Create identical API endpoints and JSON responses
- [ ] Add Go-specific optimizations (goroutines, connection pooling)

### 8. Implement Elixir version of postal code API
- [ ] Create `elixir/` directory with Mix project
- [ ] Set up Phoenix framework or plain Plug application
- [ ] Configure Ecto for database access
- [ ] Implement matching API endpoints
- [ ] Add Elixir-specific optimizations (OTP, concurrency)

## Testing & Analysis

### 9. Run baseline performance tests on Flask API
- [ ] Test single-user performance (latency benchmarks)
- [ ] Test concurrent load (10, 50, 100, 500 concurrent users)
- [ ] Test different query patterns and complexity
- [ ] Measure resource usage (CPU, memory, database connections)
- [ ] Document baseline metrics and system behavior

### 10. Compare performance across all API implementations
- [ ] Run identical test suite against all implementations
- [ ] Collect comprehensive metrics (response time percentiles, throughput)
- [ ] Monitor resource usage during tests
- [ ] Test under different load patterns (sustained, spike, ramp-up)
- [ ] Document any implementation-specific issues or advantages

### 11. Document performance test results and conclusions
- [ ] Create performance comparison charts and graphs
- [ ] Analyze results: identify best/worst performing scenarios
- [ ] Document setup methodology for reproducibility
- [ ] Write conclusions about technology trade-offs
- [ ] Create final report with recommendations

---

## Notes

- **Priority**: Complete infrastructure setup (1-4) before development tasks
- **Dependencies**: Task 5 should be completed before implementing other API versions (6-8)
- **Testing**: Each implementation should be individually tested before final comparison
- **Documentation**: Keep detailed notes throughout for final analysis