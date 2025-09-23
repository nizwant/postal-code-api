from flask import Flask
from flask_cors import CORS
from database import check_database_exists
from routes import register_routes

app = Flask(__name__)

# Configure CORS to allow requests from the frontend
CORS(app, origins=['http://localhost:3000'])

# Register all routes
register_routes(app)

if __name__ == "__main__":
    if not check_database_exists():
        print("Database file postal_codes.db not found. Please run create_db.py first.")
        exit(1)

    app.run(debug=True, host="0.0.0.0", port=5001)
