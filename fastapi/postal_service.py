from database import get_db_connection
from house_number_matcher import is_house_number_in_range


def build_search_query(
    city=None,
    street=None,
    house_number=None,
    province=None,
    county=None,
    municipality=None,
    limit=100,
):
    """Build a search query with the given parameters."""
    query = "SELECT * FROM postal_codes WHERE 1=1"
    params = []

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

    # Use a larger limit since we'll filter in Python
    sql_limit = min(limit * 5, 1000) if house_number else limit
    query += " LIMIT ?"
    params.append(sql_limit)

    return query, params


def filter_by_house_number(results, house_number, limit):
    """Filter database results by house number using the range matching logic."""
    if not house_number:
        return results[:limit]

    filtered_results = []

    for row in results:
        house_numbers = row["house_numbers"]

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


def search_with_fallbacks(
    city, street, house_number, province, county, municipality, limit
):
    """Execute search with cascading fallbacks."""
    conn = get_db_connection()

    # Try main search (without house_number in SQL)
    query, params = build_search_query(
        city, street, house_number, province, county, municipality, limit
    )
    sql_results = conn.execute(query, params).fetchall()

    # Apply house number filtering in Python
    results = filter_by_house_number(sql_results, house_number, limit)

    fallback_used = False
    fallback_message = ""

    # Fallback 1: Remove house_number if present and no results
    if len(results) == 0 and house_number:
        # Re-run query without house_number considerations
        query, params = build_search_query(
            city, street, None, province, county, municipality, limit
        )
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
        query, params = build_search_query(
            city, None, None, province, county, municipality, limit
        )
        results = conn.execute(query, params).fetchall()
        if len(results) > 0:
            fallback_used = True
            if house_number:
                fallback_message = f"Street '{street}' with house number '{house_number}' not found in {city}. Showing all results for {city}."
            else:
                fallback_message = f"Street '{street}' not found in {city}. Showing all results for {city}."

    conn.close()
    return results, fallback_used, fallback_message


def search_postal_codes(
    city=None,
    street=None,
    house_number=None,
    province=None,
    county=None,
    municipality=None,
    limit=100,
):
    """Search postal codes with given parameters."""
    results, fallback_used, fallback_message = search_with_fallbacks(
        city, street, house_number, province, county, municipality, limit
    )

    # Format results
    postal_codes = []
    for row in results:
        postal_codes.append(
            {
                "postal_code": row["postal_code"],
                "city": row["city"],
                "street": row["street"],
                "house_numbers": row["house_numbers"],
                "municipality": row["municipality"],
                "county": row["county"],
                "province": row["province"],
            }
        )

    response = {"results": postal_codes, "count": len(postal_codes)}

    if fallback_used:
        response["message"] = fallback_message
        response["fallback_used"] = True

    return response


def get_postal_code_by_code(postal_code):
    """Get postal code records by postal code."""
    conn = get_db_connection()
    results = conn.execute(
        "SELECT * FROM postal_codes WHERE postal_code = ?", (postal_code,)
    ).fetchall()
    conn.close()

    if not results:
        return None

    postal_codes = []
    for row in results:
        postal_codes.append(
            {
                "postal_code": row["postal_code"],
                "city": row["city"],
                "street": row["street"],
                "house_numbers": row["house_numbers"],
                "municipality": row["municipality"],
                "county": row["county"],
                "province": row["province"],
            }
        )

    return {"results": postal_codes, "count": len(postal_codes)}


def get_provinces():
    """Get all provinces."""
    conn = get_db_connection()
    provinces = conn.execute(
        "SELECT DISTINCT province FROM postal_codes WHERE province IS NOT NULL ORDER BY province"
    ).fetchall()
    conn.close()

    return {
        "provinces": [row["province"] for row in provinces],
        "count": len(provinces),
    }


def get_counties(province=None):
    """Get counties, optionally filtered by province."""
    conn = get_db_connection()
    if province:
        counties = conn.execute(
            "SELECT DISTINCT county FROM postal_codes WHERE county IS NOT NULL AND LOWER(province) = LOWER(?) ORDER BY county",
            (province,),
        ).fetchall()
    else:
        counties = conn.execute(
            "SELECT DISTINCT county FROM postal_codes WHERE county IS NOT NULL ORDER BY county"
        ).fetchall()
    conn.close()

    return {
        "counties": [row["county"] for row in counties],
        "count": len(counties),
        "filtered_by_province": province if province else None,
    }


def get_municipalities(province=None, county=None):
    """Get municipalities, optionally filtered by province and county."""
    query = (
        "SELECT DISTINCT municipality FROM postal_codes WHERE municipality IS NOT NULL"
    )
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

    return {
        "municipalities": [row["municipality"] for row in municipalities],
        "count": len(municipalities),
        "filtered_by_province": province if province else None,
        "filtered_by_county": county if county else None,
    }


def get_cities(province=None, county=None, municipality=None):
    """Get cities, optionally filtered by province, county, and municipality."""
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

    return {
        "cities": [row["city"] for row in cities],
        "count": len(cities),
        "filtered_by_province": province if province else None,
        "filtered_by_county": county if county else None,
        "filtered_by_municipality": municipality if municipality else None,
    }