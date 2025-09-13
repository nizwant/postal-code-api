from flask import Flask, request, jsonify
import sqlite3
import os
from house_number_matcher import is_house_number_in_range

app = Flask(__name__)

DB_PATH = 'postal_codes.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def build_search_query(city=None, street=None, house_number=None, province=None, county=None, municipality=None, limit=100):
    """
    Build a search query with the given parameters.

    Note: house_number filtering is now done in Python using is_house_number_in_range()
    instead of in SQL, so we don't include it in the SQL query.
    """
    query = "SELECT * FROM postal_codes WHERE 1=1"
    params = []

    if city:
        query += " AND LOWER(city) LIKE LOWER(?)"
        params.append(f"{city}%")

    if street:
        query += " AND LOWER(street) = LOWER(?)"
        params.append(street)

    # Note: house_number filtering moved to Python layer

    if province:
        query += " AND LOWER(province) = LOWER(?)"
        params.append(province)

    if county:
        query += " AND LOWER(county) = LOWER(?)"
        params.append(county)

    if municipality:
        query += " AND LOWER(municipality) = LOWER(?)"
        params.append(municipality)

    # Use a larger limit since we'll filter in Python
    # But still cap it to prevent excessive memory usage
    sql_limit = min(limit * 5, 1000) if house_number else limit
    query += " LIMIT ?"
    params.append(sql_limit)

    return query, params

def filter_by_house_number(results, house_number, limit):
    """
    Filter database results by house number using the range matching logic.

    Args:
        results: List of database rows
        house_number: House number to match
        limit: Maximum number of results to return

    Returns:
        Filtered list of results
    """
    if not house_number:
        return results[:limit]

    filtered_results = []

    for row in results:
        house_numbers = row['house_numbers']

        # Records without house_numbers don't match specific house number searches
        if not house_numbers:
            continue

        # Use the range matching logic
        if is_house_number_in_range(house_number, house_numbers):
            filtered_results.append(row)

            # Stop when we have enough results
            if len(filtered_results) >= limit:
                break

    return filtered_results

def search_with_fallbacks(city, street, house_number, province, county, municipality, limit):
    """Execute search with cascading fallbacks."""
    conn = get_db_connection()

    # Try main search (without house_number in SQL)
    query, params = build_search_query(city, street, house_number, province, county, municipality, limit)
    sql_results = conn.execute(query, params).fetchall()

    # Apply house number filtering in Python
    results = filter_by_house_number(sql_results, house_number, limit)

    fallback_used = False
    fallback_message = ""

    # Fallback 1: Remove house_number if present and no results
    if len(results) == 0 and house_number:
        # Re-run query without house_number considerations
        query, params = build_search_query(city, street, None, province, county, municipality, limit)
        results = conn.execute(query, params).fetchall()
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
        query, params = build_search_query(city, None, None, province, county, municipality, limit)
        results = conn.execute(query, params).fetchall()
        if len(results) > 0:
            fallback_used = True
            if house_number:
                fallback_message = f"Street '{street}' with house number '{house_number}' not found in {city}. Showing all results for {city}."
            else:
                fallback_message = f"Street '{street}' not found in {city}. Showing all results for {city}."

    conn.close()
    return results, fallback_used, fallback_message

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
    
    # Execute search with fallbacks
    results, fallback_used, fallback_message = search_with_fallbacks(
        city, street, house_number, province, county, municipality, limit
    )
    
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