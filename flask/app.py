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
        query += " AND LOWER(city) LIKE LOWER(?)"
        params.append(f"{city}%")
    
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
    
    # Cascading fallback logic
    fallback_used = False
    fallback_message = ""
    
    # Fallback 1: Remove house_number if present and no results
    if len(results) == 0 and house_number:
        fallback_query = "SELECT * FROM postal_codes WHERE 1=1"
        fallback_params = []
        
        if city:
            fallback_query += " AND LOWER(city) LIKE LOWER(?)"
            fallback_params.append(f"{city}%")
        
        if street:
            fallback_query += " AND LOWER(street) = LOWER(?)"
            fallback_params.append(street)
        
        if province:
            fallback_query += " AND LOWER(province) = LOWER(?)"
            fallback_params.append(province)
        
        if county:
            fallback_query += " AND LOWER(county) = LOWER(?)"
            fallback_params.append(county)
        
        if municipality:
            fallback_query += " AND LOWER(municipality) = LOWER(?)"
            fallback_params.append(municipality)
        
        fallback_query += " LIMIT ?"
        fallback_params.append(limit)
        
        results = conn.execute(fallback_query, fallback_params).fetchall()
        if len(results) > 0:
            fallback_used = True
            location_desc = []
            if street:
                location_desc.append(f"street '{street}'")
            if city:
                location_desc.append(f"city '{city}'")
            location_str = " in " + " in ".join(location_desc) if location_desc else ""
            fallback_message = f"House number '{house_number}' not found{location_str}. Showing all results{location_str}."
    
    # Fallback 2: Remove street if still no results and we have city + street
    if len(results) == 0 and city and street:
        fallback_query = "SELECT * FROM postal_codes WHERE 1=1"
        fallback_params = []
        
        fallback_query += " AND LOWER(city) LIKE LOWER(?)"
        fallback_params.append(f"{city}%")
        
        if province:
            fallback_query += " AND LOWER(province) = LOWER(?)"
            fallback_params.append(province)
        
        if county:
            fallback_query += " AND LOWER(county) = LOWER(?)"
            fallback_params.append(county)
        
        if municipality:
            fallback_query += " AND LOWER(municipality) = LOWER(?)"
            fallback_params.append(municipality)
        
        fallback_query += " LIMIT ?"
        fallback_params.append(limit)
        
        results = conn.execute(fallback_query, fallback_params).fetchall()
        if len(results) > 0:
            fallback_used = True
            if house_number:
                fallback_message = f"Street '{street}' with house number '{house_number}' not found in {city}. Showing all results for {city}."
            else:
                fallback_message = f"Street '{street}' not found in {city}. Showing all results for {city}."
    
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
    
    response = {
        'results': postal_codes,
        'count': len(postal_codes)
    }
    
    if fallback_used:
        response['message'] = fallback_message
        response['fallback_used'] = True
    
    return jsonify(response)

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
    return jsonify({
        'available_endpoints': {
            'provinces': '/locations/provinces',
            'counties': '/locations/counties', 
            'municipalities': '/locations/municipalities',
            'cities': '/locations/cities'
        }
    })

@app.route('/locations/provinces', methods=['GET'])
def get_provinces():
    conn = get_db_connection()
    provinces = conn.execute(
        "SELECT DISTINCT province FROM postal_codes WHERE province IS NOT NULL ORDER BY province"
    ).fetchall()
    conn.close()
    
    return jsonify({
        'provinces': [row['province'] for row in provinces],
        'count': len(provinces)
    })

@app.route('/locations/counties', methods=['GET'])
def get_counties():
    province = request.args.get('province')
    
    conn = get_db_connection()
    if province:
        counties = conn.execute(
            "SELECT DISTINCT county FROM postal_codes WHERE county IS NOT NULL AND LOWER(province) = LOWER(?) ORDER BY county",
            (province,)
        ).fetchall()
    else:
        counties = conn.execute(
            "SELECT DISTINCT county FROM postal_codes WHERE county IS NOT NULL ORDER BY county"
        ).fetchall()
    conn.close()
    
    return jsonify({
        'counties': [row['county'] for row in counties],
        'count': len(counties),
        'filtered_by_province': province if province else None
    })

@app.route('/locations/municipalities', methods=['GET'])
def get_municipalities():
    province = request.args.get('province')
    county = request.args.get('county')
    
    query = "SELECT DISTINCT municipality FROM postal_codes WHERE municipality IS NOT NULL"
    params = []
    
    if province:
        query += " AND LOWER(province) = LOWER(?)"
        params.append(province)
    
    if county:
        query += " AND LOWER(county) = LOWER(?)"
        params.append(county)
    
    query += " ORDER BY municipality"
    
    conn = get_db_connection()
    municipalities = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify({
        'municipalities': [row['municipality'] for row in municipalities],
        'count': len(municipalities),
        'filtered_by_province': province if province else None,
        'filtered_by_county': county if county else None
    })

@app.route('/locations/cities', methods=['GET'])
def get_cities():
    province = request.args.get('province')
    county = request.args.get('county')
    municipality = request.args.get('municipality')
    
    query = "SELECT DISTINCT city FROM postal_codes WHERE city IS NOT NULL"
    params = []
    
    if province:
        query += " AND LOWER(province) = LOWER(?)"
        params.append(province)
    
    if county:
        query += " AND LOWER(county) = LOWER(?)"
        params.append(county)
    
    if municipality:
        query += " AND LOWER(municipality) = LOWER(?)"
        params.append(municipality)
    
    query += " ORDER BY city"
    
    conn = get_db_connection()
    cities = conn.execute(query, params).fetchall()
    conn.close()
    
    return jsonify({
        'cities': [row['city'] for row in cities],
        'count': len(cities),
        'filtered_by_province': province if province else None,
        'filtered_by_county': county if county else None,
        'filtered_by_municipality': municipality if municipality else None
    })

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"Database file {DB_PATH} not found. Please run create_db.py first.")
        exit(1)
    
    app.run(debug=True, host='0.0.0.0', port=5001)