# FastAPI Implementation

This is the FastAPI implementation of the Polish postal code API, designed for performance comparison with other technologies.

## Setup

```bash
cd fastapi
pip install -r requirements.txt
```

## Running

### Development Server (localhost:5002)
```bash
python main.py
```

### Production Server (recommended for benchmarking)
```bash
pip install gunicorn
gunicorn app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5002
```

## API Endpoints

Same endpoints as Flask implementation:

- `GET /postal-codes` - Multi-parameter search
- `GET /postal-codes/{code}` - Direct postal code lookup
- `GET /locations/*` - Hierarchical location endpoints
- `GET /health` - Health check

## Features

- **Same Database**: Reuses `../postal_codes.db` (122k records)
- **Same Logic**: Identical house number matching and search fallbacks
- **Same API**: Compatible endpoints and response format
- **FastAPI Benefits**: Automatic API documentation at `/docs`, type validation, async support
- **Production Ready**: Configured for port 5002 with Gunicorn + Uvicorn workers

## Testing

Test the implementation:
```bash
python test_basic.py
```

## API Documentation

When running, visit `http://localhost:5002/docs` for interactive API documentation.