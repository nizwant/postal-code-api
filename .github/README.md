# CI/CD Pipeline Documentation

This repository uses GitHub Actions for continuous integration across all API implementations.

## Overview

The CI/CD pipeline is designed to:
- Test each API implementation independently
- Run security scans and performance tests
- Build production artifacts
- Ensure API consistency across implementations
- Support multiple programming language ecosystems

## Workflows

### 1. Main CI Pipeline (`main-ci.yml`)
- **Trigger**: Push to `main`/`develop`, Pull requests
- **Purpose**: Orchestrates all other workflows
- **Features**:
  - Path-based filtering (only runs workflows for changed code)
  - Cross-API integration testing
  - CI summary reporting

### 2. Flask CI (`flask-ci.yml`)
- **Trigger**: Changes to `flask/` directory
- **Python versions**: 3.9, 3.10, 3.11
- **Features**:
  - Linting (flake8) and formatting (black)
  - Unit tests with coverage
  - API endpoint testing
  - Security scanning (bandit, safety)
  - Production server testing (Gunicorn)

### 3. FastAPI CI (`fastapi-ci.yml`)
- **Trigger**: Changes to `fastapi/` directory
- **Python versions**: 3.9, 3.10, 3.11
- **Features**:
  - Async testing with pytest-asyncio
  - OpenAPI documentation testing
  - Performance testing with wrk
  - Multiple server configurations (Uvicorn, Gunicorn+Uvicorn)

### 4. Go CI (`go-ci.yml`)
- **Trigger**: Changes to `go/` directory
- **Go versions**: 1.20, 1.21, 1.22
- **Features**:
  - Cross-compilation for multiple platforms
  - Static analysis (staticcheck, golangci-lint)
  - Security scanning (gosec, govulncheck)
  - Benchmark testing
  - Race condition detection

### 5. Elixir CI (`elixir-ci.yml`)
- **Trigger**: Changes to `elixir/` directory
- **Elixir versions**: 1.14, 1.15, 1.16
- **OTP versions**: 25, 26
- **Features**:
  - Database testing with PostgreSQL
  - Type checking (Dialyzer)
  - Code quality (Credo)
  - Security analysis (Sobelow)
  - Release building and testing

## CI Features

### Path-Based Execution
Workflows only run when relevant files change:
```yaml
paths:
  - 'flask/**'
  - '.github/workflows/flask-ci.yml'
```

### Security Scanning
Each language has appropriate security tools:
- **Python**: bandit (SAST), safety (dependencies)
- **Go**: gosec (SAST), govulncheck (dependencies)
- **Elixir**: sobelow (Phoenix security)

### Performance Testing
Basic performance tests using `wrk`:
- Load testing with concurrent connections
- Response time measurement
- Throughput analysis

### Multi-Platform Builds
Go API builds for multiple platforms:
- Linux (amd64, arm64)
- macOS (amd64, arm64) 
- Windows (amd64)

### Cross-API Integration
Tests API consistency:
- Same endpoints return similar data structures
- Status codes are consistent
- Response times are reasonable

## Artifacts

Each successful build produces artifacts:
- **Flask/FastAPI**: Python source + dependencies
- **Go**: Compiled binaries for multiple platforms
- **Elixir**: OTP releases

## Configuration Files

### `.github/dependabot.yml` (Recommended)
```yaml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/flask"
    schedule:
      interval: "weekly"
  
  - package-ecosystem: "pip"
    directory: "/fastapi"
    schedule:
      interval: "weekly"
      
  - package-ecosystem: "gomod"
    directory: "/go"
    schedule:
      interval: "weekly"
      
  - package-ecosystem: "mix"
    directory: "/elixir"
    schedule:
      interval: "weekly"
```

## Environment Variables

### Required for Production
- `SECRET_KEY_BASE` (Elixir)
- `DATABASE_URL` (All apps)
- `PHX_HOST`, `PHX_PORT` (Elixir)

### Optional for CI
- `CODECOV_TOKEN` (Coverage reporting)

## Local Development

### Testing Individual Apps
```bash
# Flask
cd flask && python -m pytest

# FastAPI (when implemented)
cd fastapi && python -m pytest

# Go (when implemented)
cd go && go test ./...

# Elixir (when implemented)
cd elixir && mix test
```

### Running CI Tests Locally

#### Using Act (GitHub Actions locally)
```bash
# Install act: https://github.com/nektos/act
act push
```

#### Manual Testing
```bash
# Test Flask
cd flask
pip install -r requirements.txt
python create_db.py
python -m pytest
python app.py &
curl http://localhost:5001/health
```

## Deployment Integration

### Staging Environment
- Triggered on successful CI for `develop` branch
- Uses test database with sample data
- Runs integration tests

### Production Environment
- Triggered on successful CI for `main` branch
- Requires manual approval
- Uses production database
- Includes rollback mechanism

## Monitoring

### CI Health
- Build success/failure rates
- Test execution times
- Security scan results
- Performance trends

### API Health (Production)
- Response time monitoring
- Error rate tracking
- Resource usage (CPU, memory)
- Database performance

## Troubleshooting

### Common Issues

1. **Tests failing locally but passing in CI**
   - Check Python/Go/Elixir version differences
   - Verify dependency versions
   - Check environment variables

2. **Security scans failing**
   - Update dependencies to patch vulnerabilities
   - Add exceptions for false positives (with justification)

3. **Performance tests failing**
   - Check if test data is consistent
   - Verify resource constraints in CI environment
   - Review baseline expectations

### Getting Help
- Check workflow logs in GitHub Actions
- Review individual test outputs
- Compare with previous successful runs
- Contact maintainers via issues