from fastapi import FastAPI
from database import check_database_exists
from routes import router
import sys

app = FastAPI(
    title="Polish Postal Code API (FastAPI)",
    description="FastAPI implementation for Polish postal code lookups with sophisticated house number matching",
    version="1.0.0"
)

# Include routes
app.include_router(router)

@app.on_event("startup")
def startup_event():
    """Check database exists on startup."""
    if not check_database_exists():
        print("Database file postal_codes.db not found. Please run create_db.py first.")
        sys.exit(1)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5002)