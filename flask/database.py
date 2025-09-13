import sqlite3
import os

DB_PATH = 'postal_codes.db'

def get_db_connection():
    """Get a database connection with row factory configured."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_database_exists():
    """Check if the database file exists."""
    return os.path.exists(DB_PATH)