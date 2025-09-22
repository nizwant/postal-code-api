from database import get_db_connection
from house_number_matcher import is_house_number_in_range
from polish_normalizer import get_normalized_search_params


def build_search_query(
    city=None,
    street=None,
    house_number=None,
    province=None,
    county=None,
    municipality=None,
    limit=100,
    use_normalized=False,
):
    """Build a search query with the given parameters."""
    query = "SELECT * FROM postal_codes WHERE 1=1"
    params = []

    # Choose column names based on whether we're using normalized search
    # Always use city_clean for filtering (not original city)
    city_col = "city_normalized" if use_normalized else "city_clean"
    street_col = "street_normalized" if use_normalized else "street"

    if city:
        query += f" AND {city_col} LIKE ? COLLATE NOCASE"
        params.append(f"{city}%")

    if street:
        query += f" AND {street_col} LIKE ? COLLATE NOCASE"
        params.append(f"%{street}%")

    if province:
        query += " AND province = ? COLLATE NOCASE"
        params.append(province)

    if county:
        query += " AND county = ? COLLATE NOCASE"
        params.append(county)

    if municipality:
        query += " AND municipality = ? COLLATE NOCASE"
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


def execute_fallback_search(
    city, street, house_number, province, county, municipality, limit, use_normalized=False
):
    """Execute fallback search logic when initial search returned no results."""
    conn = get_db_connection()

    fallback_used = False
    fallback_message = ""
    results = []

    # Fallback 1: Remove house_number if present
    if house_number:
        # Re-run query without house_number considerations
        query, params = build_search_query(
            city, street, None, province, county, municipality, limit, use_normalized
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
            city, None, None, province, county, municipality, limit, use_normalized
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
    """Search postal codes with four-tier approach: exact, Polish normalization, fallbacks, then Polish fallbacks."""

    # Pre-calculate normalized parameters once (eliminates duplication)
    normalized_params = get_normalized_search_params(
        city=city,
        street=street,
        house_number=house_number,
        province=province,
        county=county,
        municipality=municipality,
        limit=limit
    )

    # Extract normalized parameters to variables to reduce repetitive .get() calls
    norm_city = normalized_params.get('city')
    norm_street = normalized_params.get('street')
    norm_house = normalized_params.get('house_number')
    norm_province = normalized_params.get('province')
    norm_county = normalized_params.get('county')
    norm_municipality = normalized_params.get('municipality')
    norm_limit = normalized_params.get('limit', limit)

    polish_fallback_used = False
    search_type = "exact"
    fallback_used = False
    fallback_message = ""

    # Tier 1: Exact search with original parameters
    with get_db_connection() as conn:
        query, params = build_search_query(
            city, street, house_number, province, county, municipality, limit
        )
        sql_results = conn.execute(query, params).fetchall()
        exact_results = filter_by_house_number(sql_results, house_number, limit)

    if len(exact_results) > 0:
        results = exact_results
    else:
        # Tier 2: Polish character normalization search
        with get_db_connection() as conn:
            query, params = build_search_query(
                norm_city, norm_street, norm_house, norm_province, norm_county, norm_municipality, norm_limit,
                use_normalized=True
            )
            sql_results = conn.execute(query, params).fetchall()
            polish_results = filter_by_house_number(sql_results, norm_house, limit)

        if len(polish_results) > 0:
            results = polish_results
            polish_fallback_used = True
            search_type = "polish_characters"
        else:
            # Tier 3: Original fallback logic (house_number → street → city-only)
            results, fallback_used, fallback_message = execute_fallback_search(
                city, street, house_number, province, county, municipality, limit
            )

            # Tier 4: Polish normalization fallback logic (only if Tier 3 failed)
            if len(results) == 0:
                # Search using normalized columns with fallback logic
                tier4_results, tier4_fallback_used, tier4_fallback_message = execute_fallback_search(
                    norm_city, norm_street, norm_house, norm_province, norm_county, norm_municipality, norm_limit,
                    use_normalized=True
                )

                if len(tier4_results) > 0:
                    results = tier4_results
                    fallback_used = tier4_fallback_used
                    fallback_message = tier4_fallback_message
                    polish_fallback_used = True
                    search_type = "polish_characters"

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

    response = {
        "results": postal_codes,
        "count": len(postal_codes),
        "search_type": search_type
    }

    if fallback_used:
        response["message"] = fallback_message
        response["fallback_used"] = True

    if polish_fallback_used:
        if "message" in response:
            response["message"] += " Polish characters were normalized for search."
        else:
            response["message"] = "Search performed with Polish character normalization."
        response["polish_normalization_used"] = True

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


def get_provinces(prefix=None):
    """Get all provinces, optionally filtered by prefix."""
    with get_db_connection() as conn:
        provinces = conn.execute(
            "SELECT DISTINCT province FROM postal_codes WHERE province IS NOT NULL ORDER BY province"
        ).fetchall()

        if prefix:
            # Filter provinces with Polish character normalization
            from polish_normalizer import normalize_polish_text
            normalized_prefix = normalize_polish_text(prefix).lower()
            original_prefix = prefix.lower()

            # Filter provinces that start with either original or normalized prefix
            filtered_provinces = [
                row for row in provinces
                if (row["province"].lower().startswith(original_prefix) or
                    normalize_polish_text(row["province"]).lower().startswith(normalized_prefix))
            ]
        else:
            filtered_provinces = provinces

    return {
        "provinces": [row["province"] for row in filtered_provinces],
        "count": len(filtered_provinces),
        "filtered_by_prefix": prefix if prefix else None,
    }


def get_counties(province=None, prefix=None):
    """Get counties, optionally filtered by province and/or prefix."""
    query = "SELECT DISTINCT county FROM postal_codes WHERE county IS NOT NULL"
    params = []

    if province:
        query += " AND province = ? COLLATE NOCASE"
        params.append(province)

    query += " ORDER BY county"

    with get_db_connection() as conn:
        counties = conn.execute(query, params).fetchall()

        if prefix:
            # Filter counties with Polish character normalization
            from polish_normalizer import normalize_polish_text
            normalized_prefix = normalize_polish_text(prefix).lower()
            original_prefix = prefix.lower()

            filtered_counties = [
                row for row in counties
                if (row["county"].lower().startswith(original_prefix) or
                    normalize_polish_text(row["county"]).lower().startswith(normalized_prefix))
            ]
        else:
            filtered_counties = counties

    return {
        "counties": [row["county"] for row in filtered_counties],
        "count": len(filtered_counties),
        "filtered_by_province": province if province else None,
        "filtered_by_prefix": prefix if prefix else None,
    }


def get_municipalities(province=None, county=None, prefix=None):
    """Get municipalities, optionally filtered by province, county, and/or prefix."""
    query = "SELECT DISTINCT municipality FROM postal_codes WHERE municipality IS NOT NULL"
    params = []

    if province:
        query += " AND province = ? COLLATE NOCASE"
        params.append(province)

    if county:
        query += " AND county = ? COLLATE NOCASE"
        params.append(county)

    query += " ORDER BY municipality"

    with get_db_connection() as conn:
        municipalities = conn.execute(query, params).fetchall()

        if prefix:
            # Filter municipalities with Polish character normalization
            from polish_normalizer import normalize_polish_text
            normalized_prefix = normalize_polish_text(prefix).lower()
            original_prefix = prefix.lower()

            filtered_municipalities = [
                row for row in municipalities
                if (row["municipality"].lower().startswith(original_prefix) or
                    normalize_polish_text(row["municipality"]).lower().startswith(normalized_prefix))
            ]
        else:
            filtered_municipalities = municipalities

    return {
        "municipalities": [row["municipality"] for row in filtered_municipalities],
        "count": len(filtered_municipalities),
        "filtered_by_province": province if province else None,
        "filtered_by_county": county if county else None,
        "filtered_by_prefix": prefix if prefix else None,
    }


def get_cities(province=None, county=None, municipality=None, prefix=None):
    """Get cities, optionally filtered by province, county, municipality, and/or prefix."""
    query = "SELECT DISTINCT city_clean FROM postal_codes WHERE city_clean IS NOT NULL"
    params = []

    if province:
        query += " AND province = ? COLLATE NOCASE"
        params.append(province)

    if county:
        query += " AND county = ? COLLATE NOCASE"
        params.append(county)

    if municipality:
        query += " AND municipality = ? COLLATE NOCASE"
        params.append(municipality)

    if prefix:
        # Use both city_clean and city_normalized for prefix matching (supports Polish chars)
        from polish_normalizer import normalize_polish_text
        normalized_prefix = normalize_polish_text(prefix)
        query += " AND (city_clean LIKE ? COLLATE NOCASE OR city_normalized LIKE ? COLLATE NOCASE)"
        params.extend([f"{prefix}%", f"{normalized_prefix}%"])

    query += " ORDER BY population DESC, city_clean"

    with get_db_connection() as conn:
        cities = conn.execute(query, params).fetchall()

    return {
        "cities": [row["city_clean"] for row in cities],
        "count": len(cities),
        "filtered_by_province": province if province else None,
        "filtered_by_county": county if county else None,
        "filtered_by_municipality": municipality if municipality else None,
        "filtered_by_prefix": prefix if prefix else None,
    }


def get_streets(city=None, province=None, county=None, municipality=None, prefix=None):
    """Get streets, optionally filtered by city, province, county, municipality, and/or prefix."""
    query = "SELECT DISTINCT street FROM postal_codes WHERE street IS NOT NULL AND street != ''"
    params = []

    if city:
        query += " AND city_clean = ? COLLATE NOCASE"
        params.append(city)

    if province:
        query += " AND province = ? COLLATE NOCASE"
        params.append(province)

    if county:
        query += " AND county = ? COLLATE NOCASE"
        params.append(county)

    if municipality:
        query += " AND municipality = ? COLLATE NOCASE"
        params.append(municipality)

    if prefix:
        # Use both original and normalized street columns for prefix matching
        from polish_normalizer import normalize_polish_text

        normalized_prefix = normalize_polish_text(prefix)
        query += (
            " AND (street LIKE ? COLLATE NOCASE OR street_normalized LIKE ? COLLATE NOCASE)"
        )
        params.extend([f"{prefix}%", f"{normalized_prefix}%"])

    query += " ORDER BY street"

    with get_db_connection() as conn:
        streets = conn.execute(query, params).fetchall()

    return {
        "streets": [row["street"] for row in streets],
        "count": len(streets),
        "filtered_by_city": city if city else None,
        "filtered_by_province": province if province else None,
        "filtered_by_county": county if county else None,
        "filtered_by_municipality": municipality if municipality else None,
        "filtered_by_prefix": prefix if prefix else None,
    }