from flask import Flask, request, jsonify
import sqlite3
import os

app = Flask(__name__)

DB_PATH = 'postal_codes.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/postal-codes', methods=['GET'])
def search_postal_codes():
    # Get query parameters
    city = request.args.get('city')
    street = request.args.get('street')
    house_number = request.args.get('house_number')
    province = request.args.get('province')
    county = request.args.get('county')
    municipality = request.args.get('municipality')
    limit = request.args.get('limit', default=100, type=int)
    
    # Build query
    query = "SELECT * FROM postal_codes WHERE 1=1"
    params = []
    
    if city:
        query += " AND LOWER(city) = LOWER(?)"
        params.append(city)
    
    if street:
        query += " AND LOWER(street) = LOWER(?)"
        params.append(street)
    
    if house_number:
        query += " AND house_numbers = ?"
        params.append(house_number)
    
    if province:
        query += " AND LOWER(province) = LOWER(?)"
        params.append(province)
    
    if county:
        query += " AND LOWER(county) = LOWER(?)"
        params.append(county)
    
    if municipality:
        query += " AND LOWER(municipality) = LOWER(?)"
        params.append(municipality)
    
    query += " LIMIT ?"
    params.append(limit)
    
    # Execute query
    conn = get_db_connection()
    results = conn.execute(query, params).fetchall()
    conn.close()
    
    # Format results
    postal_codes = []
    for row in results:
        postal_codes.append({
            'postal_code': row['postal_code'],
            'city': row['city'],
            'street': row['street'],
            'house_numbers': row['house_numbers'],
            'municipality': row['municipality'],
            'county': row['county'],
            'province': row['province']
        })
    
    return jsonify({
        'results': postal_codes,
        'count': len(postal_codes)
    })

@app.route('/postal-codes/<postal_code>', methods=['GET'])
def get_postal_code(postal_code):
    conn = get_db_connection()
    results = conn.execute(
        "SELECT * FROM postal_codes WHERE postal_code = ?",
        (postal_code,)
    ).fetchall()
    conn.close()
    
    if not results:
        return jsonify({'error': 'Postal code not found'}), 404
    
    postal_codes = []
    for row in results:
        postal_codes.append({
            'postal_code': row['postal_code'],
            'city': row['city'],
            'street': row['street'],
            'house_numbers': row['house_numbers'],
            'municipality': row['municipality'],
            'county': row['county'],
            'province': row['province']
        })
    
    return jsonify({
        'results': postal_codes,
        'count': len(postal_codes)
    })

@app.route('/locations', methods=['GET'])
def get_locations():
    conn = get_db_connection()
    
    # Get unique provinces
    provinces = conn.execute(
        "SELECT DISTINCT province FROM postal_codes WHERE province IS NOT NULL ORDER BY province"
    ).fetchall()
    
    # Get unique counties
    counties = conn.execute(
        "SELECT DISTINCT county FROM postal_codes WHERE county IS NOT NULL ORDER BY county"
    ).fetchall()
    
    # Get unique municipalities
    municipalities = conn.execute(
        "SELECT DISTINCT municipality FROM postal_codes WHERE municipality IS NOT NULL ORDER BY municipality"
    ).fetchall()
    
    # Get unique cities
    cities = conn.execute(
        "SELECT DISTINCT city FROM postal_codes WHERE city IS NOT NULL ORDER BY city"
    ).fetchall()
    
    conn.close()
    
    return jsonify({
        'provinces': [row['province'] for row in provinces],
        'counties': [row['county'] for row in counties],
        'municipalities': [row['municipality'] for row in municipalities],
        'cities': [row['city'] for row in cities]
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found. Please run create_db.py first.")
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=5001)