#!/usr/bin/env python3
"""
Enhanced Flask API for Polish Postal Code Lookup
Using Normalized Database Structure

This version uses the normalized database with parsed house ranges
for fast, accurate house number matching without complex regex parsing.
"""

from flask import Flask, request, jsonify
import sqlite3
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Database configuration
ORIGINAL_DB_PATH = 'postal_codes.db'
NORMALIZED_DB_PATH = 'postal_codes_normalized.db'

def get_db_connection(use_normalized=True):
    """Get database connection."""
    db_path = NORMALIZED_DB_PATH if use_normalized else ORIGINAL_DB_PATH
    
    if not os.path.exists(db_path):
        if use_normalized:
            logger.warning(f"Normalized database not found at {db_path}, falling back to original")
            return get_db_connection(use_normalized=False)
        else:
            raise FileNotFoundError(f"Database not found: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def search_house_number_normalized(city=None, street=None, house_number=None, 
                                 province=None, county=None, municipality=None, limit=100):
    """
    Search using the normalized database with parsed house ranges.
    
    This provides exact house number matching without regex parsing.
    """
    conn = get_db_connection(use_normalized=True)
    cursor = conn.cursor()
    
    # Build base query
    query = """
        SELECT DISTINCT postal_code, city, street, municipality, county, province,
               GROUP_CONCAT(original_range_text) as house_numbers_display
        FROM house_ranges 
        WHERE 1=1
    """
    params = []
    
    # Location filters
    if city:
        query += " AND LOWER(city) LIKE LOWER(?)"
        params.append(f"{city}%")
    
    if street:
        query += " AND LOWER(street) = LOWER(?)"
        params.append(street)
    
    if province:
        query += " AND LOWER(province) = LOWER(?)"
        params.append(province)
    
    if county:
        query += " AND LOWER(county) = LOWER(?)"
        params.append(county)
    
    if municipality:
        query += " AND LOWER(municipality) = LOWER(?)"
        params.append(municipality)
    
    # House number filtering - this is where the magic happens!
    if house_number:
        try:
            house_num_int = int(house_number)
            is_even = house_num_int % 2 == 0
            
            query += """
                AND (
                    -- House number falls within range
                    (start_number <= ? AND (end_number >= ? OR end_number IS NULL))
                    AND (
                        -- No side restriction (both odd and even allowed)
                        (is_odd IS NULL AND is_even IS NULL)
                        OR
                        -- Matches odd restriction
                        (is_odd = 1 AND ? = 1)
                        OR  
                        -- Matches even restriction
                        (is_even = 1 AND ? = 1)
                    )
                )
            """
            params.extend([house_num_int, house_num_int, 0 if is_even else 1, 1 if is_even else 0])
            
        except ValueError:
            # Handle non-numeric house numbers (4a, etc.) - search in special_cases
            query += " AND (original_range_text LIKE ? OR special_cases LIKE ?)"
            params.extend([f"%{house_number}%", f"%{house_number}%"])
    
    # Group by postal code and add limit
    query += """
        GROUP BY postal_code, city, street, municipality, county, province
        ORDER BY postal_code
        LIMIT ?
    """
    params.append(limit)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    return [dict(result) for result in results]

def search_with_fallbacks_normalized(city, street, house_number, province, county, municipality, limit):
    """
    Execute search with cascading fallbacks using normalized database.
    
    1. Try exact match with all parameters
    2. If no results and house_number provided, remove house_number
    3. If still no results and street provided, remove street
    """
    # Try exact search first
    results = search_house_number_normalized(
        city=city, street=street, house_number=house_number,
        province=province, county=county, municipality=municipality, limit=limit
    )
    
    # Return results with metadata
    response = {
        "count": len(results),
        "results": results,
        "fallback_used": False,
        "message": None
    }
    
    if results:
        return response
    
    # Fallback 1: Remove house number
    if house_number:
        logger.info(f"No exact match for house number '{house_number}', trying without house number")
        results = search_house_number_normalized(
            city=city, street=street, house_number=None,
            province=province, county=county, municipality=municipality, limit=limit
        )
        
        if results:
            location_desc = f"street '{street}' in city '{city}'" if street else f"city '{city}'"
            response.update({
                "count": len(results),
                "results": results,
                "fallback_used": True,
                "message": f"House number '{house_number}' not found in {location_desc}. Showing all results in {location_desc}."
            })
            return response
    
    # Fallback 2: Remove street as well
    if street:
        logger.info(f"No results for street '{street}', trying city only")
        results = search_house_number_normalized(
            city=city, street=None, house_number=None,
            province=province, county=county, municipality=municipality, limit=limit
        )
        
        if results:
            response.update({
                "count": len(results),
                "results": results,
                "fallback_used": True,
                "message": f"Street '{street}' not found in city '{city}'. Showing all results in city '{city}'."
            })
            return response
    
    return response

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        # Test both databases
        with get_db_connection(use_normalized=True) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM house_ranges")
            normalized_count = cursor.fetchone()[0]
        
        with get_db_connection(use_normalized=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM postal_codes")
            original_count = cursor.fetchone()[0]
        
        return jsonify({
            "status": "healthy",
            "database": "normalized",
            "original_records": original_count,
            "normalized_ranges": normalized_count
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/postal-codes', methods=['GET'])
def search_postal_codes():
    """
    Search postal codes with house number matching.
    
    Parameters:
    - city: City name (partial matching supported)
    - street: Street name (exact matching)  
    - house_number: House number (smart range matching)
    - province: Province name (exact matching)
    - county: County name (exact matching)
    - municipality: Municipality name (exact matching)
    - limit: Maximum number of results (default: 100)
    """
    try:
        # Extract parameters
        city = request.args.get('city')
        street = request.args.get('street')
        house_number = request.args.get('house_number')
        province = request.args.get('province')
        county = request.args.get('county')
        municipality = request.args.get('municipality')
        limit = int(request.args.get('limit', 100))
        
        # Validate limit
        if limit > 1000:
            limit = 1000
        
        # Perform search with fallbacks
        response = search_with_fallbacks_normalized(
            city, street, house_number, province, county, municipality, limit
        )
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in postal code search: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/postal-codes/<postal_code>', methods=['GET'])
def get_postal_code(postal_code):
    """Get details for a specific postal code."""
    try:
        conn = get_db_connection(use_normalized=True)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT postal_code, city, street, municipality, county, province,
                   GROUP_CONCAT(original_range_text) as house_numbers_display
            FROM house_ranges 
            WHERE postal_code = ?
            GROUP BY postal_code, city, street, municipality, county, province
            ORDER BY city, street
        """, (postal_code,))
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return jsonify({"error": "Postal code not found"}), 404
        
        return jsonify({
            "postal_code": postal_code,
            "count": len(results),
            "results": [dict(result) for result in results]
        })
        
    except Exception as e:
        logger.error(f"Error in postal code lookup: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

# Location hierarchy endpoints (using original database for compatibility)
@app.route('/locations', methods=['GET'])
def get_locations():
    """Get available location endpoints."""
    return jsonify({
        "endpoints": {
            "/locations/provinces": "Get all provinces",
            "/locations/counties": "Get counties, optionally filtered by province",
            "/locations/municipalities": "Get municipalities, optionally filtered by province and county",
            "/locations/cities": "Get cities, optionally filtered by province, county, and municipality"
        }
    })

@app.route('/locations/provinces', methods=['GET'])
def get_provinces():
    """Get all provinces."""
    try:
        conn = get_db_connection(use_normalized=False)  # Use original for compatibility
        cursor = conn.cursor()
        
        cursor.execute("SELECT DISTINCT province FROM postal_codes WHERE province IS NOT NULL ORDER BY province")
        results = cursor.fetchall()
        conn.close()
        
        provinces = [row[0] for row in results]
        return jsonify({"provinces": provinces})
        
    except Exception as e:
        logger.error(f"Error getting provinces: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/locations/counties', methods=['GET'])
def get_counties():
    """Get counties, optionally filtered by province."""
    try:
        province = request.args.get('province')
        
        conn = get_db_connection(use_normalized=False)
        cursor = conn.cursor()
        
        if province:
            cursor.execute("""
                SELECT DISTINCT county FROM postal_codes 
                WHERE county IS NOT NULL AND LOWER(province) = LOWER(?)
                ORDER BY county
            """, (province,))
        else:
            cursor.execute("SELECT DISTINCT county FROM postal_codes WHERE county IS NOT NULL ORDER BY county")
        
        results = cursor.fetchall()
        conn.close()
        
        counties = [row[0] for row in results]
        response = {"counties": counties}
        if province:
            response["filtered_by_province"] = province
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting counties: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/locations/municipalities', methods=['GET'])
def get_municipalities():
    """Get municipalities, optionally filtered by province and county."""
    try:
        province = request.args.get('province')
        county = request.args.get('county')
        
        conn = get_db_connection(use_normalized=False)
        cursor = conn.cursor()
        
        query = "SELECT DISTINCT municipality FROM postal_codes WHERE municipality IS NOT NULL"
        params = []
        
        if province:
            query += " AND LOWER(province) = LOWER(?)"
            params.append(province)
        
        if county:
            query += " AND LOWER(county) = LOWER(?)"
            params.append(county)
        
        query += " ORDER BY municipality"
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        municipalities = [row[0] for row in results]
        response = {"municipalities": municipalities}
        if province:
            response["filtered_by_province"] = province
        if county:
            response["filtered_by_county"] = county
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting municipalities: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/locations/cities', methods=['GET'])
def get_cities():
    """Get cities, optionally filtered by province, county, and municipality."""
    try:
        province = request.args.get('province')
        county = request.args.get('county')
        municipality = request.args.get('municipality')
        limit = int(request.args.get('limit', 1000))
        
        conn = get_db_connection(use_normalized=False)
        cursor = conn.cursor()
        
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
        
        query += " ORDER BY city LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        cities = [row[0] for row in results]
        response = {"cities": cities}
        if province:
            response["filtered_by_province"] = province
        if county:
            response["filtered_by_county"] = county
        if municipality:
            response["filtered_by_municipality"] = municipality
            
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting cities: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

@app.route('/stats', methods=['GET'])
def get_statistics():
    """Get database statistics and migration info."""
    try:
        stats = {}
        
        # Original database stats
        with get_db_connection(use_normalized=False) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM postal_codes")
            stats["original_records"] = cursor.fetchone()[0]
        
        # Normalized database stats
        try:
            with get_db_connection(use_normalized=True) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM house_ranges")
                stats["normalized_ranges"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE range_type = 'dk'")
                stats["dk_ranges"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE is_odd = 1")
                stats["odd_ranges"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE is_even = 1") 
                stats["even_ranges"] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE range_type = 'complex'")
                stats["complex_ranges"] = cursor.fetchone()[0]
                
                # Migration stats
                cursor.execute("""
                    SELECT migration_date, original_records, normalized_records, 
                           parsing_errors, complex_patterns 
                    FROM migration_stats 
                    ORDER BY migration_date DESC 
                    LIMIT 1
                """)
                migration_result = cursor.fetchone()
                
                if migration_result:
                    stats["migration"] = {
                        "date": migration_result[0],
                        "original_records": migration_result[1], 
                        "normalized_records": migration_result[2],
                        "parsing_errors": migration_result[3],
                        "complex_patterns": migration_result[4]
                    }
        
        except Exception as e:
            stats["normalized_database_error"] = str(e)
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500

if __name__ == '__main__':
    # Check if normalized database exists
    if not os.path.exists(NORMALIZED_DB_PATH):
        logger.warning(f"Normalized database not found at {NORMALIZED_DB_PATH}")
        logger.warning("Please run: python create_normalized_db.py")
        logger.warning("Falling back to original database for now...")
    
    app.run(debug=True, host='0.0.0.0', port=5001)