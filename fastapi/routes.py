from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from postal_service import (
    search_postal_codes,
    get_postal_code_by_code,
    get_provinces,
    get_counties,
    get_municipalities,
    get_cities,
    get_streets,
)

router = APIRouter()


def trim_param(value: Optional[str]) -> Optional[str]:
    """Trim whitespace from parameter value if it exists"""
    return value.strip() if value else value


@router.get("/postal-codes")
def search_postal_codes_route(
    city: str = Query(..., description="City name (required)"),
    street: Optional[str] = Query(None),
    house_number: Optional[str] = Query(None),
    province: Optional[str] = Query(None),
    county: Optional[str] = Query(None),
    municipality: Optional[str] = Query(None),
    limit: int = Query(100, ge=1),
):
    """Search postal codes with given parameters."""
    # Trim whitespace from city parameter and validate
    city_trimmed = trim_param(city)
    if not city_trimmed:
        raise HTTPException(status_code=400, detail="City parameter is required")

    # Trim whitespace from all other string parameters
    response = search_postal_codes(
        city=city_trimmed,
        street=trim_param(street),
        house_number=trim_param(house_number),
        province=trim_param(province),
        county=trim_param(county),
        municipality=trim_param(municipality),
        limit=limit,
    )

    return response


@router.get("/postal-codes/{postal_code}")
def get_postal_code_route(postal_code: str):
    """Get postal code records by postal code."""
    result = get_postal_code_by_code(postal_code)

    if not result:
        raise HTTPException(status_code=404, detail="Postal code not found")

    return result


@router.get("/locations")
def get_locations():
    """Get available location endpoints."""
    return {
        "available_endpoints": {
            "provinces": "/locations/provinces",
            "counties": "/locations/counties",
            "municipalities": "/locations/municipalities",
            "cities": "/locations/cities",
            "streets": "/locations/streets",
        }
    }


@router.get("/locations/provinces")
def get_provinces_route(prefix: Optional[str] = Query(None)):
    """Get all provinces."""
    return get_provinces(prefix=trim_param(prefix))


@router.get("/locations/counties")
def get_counties_route(
    province: Optional[str] = Query(None), prefix: Optional[str] = Query(None)
):
    """Get counties, optionally filtered by province."""
    return get_counties(province=trim_param(province), prefix=trim_param(prefix))


@router.get("/locations/municipalities")
def get_municipalities_route(
    province: Optional[str] = Query(None),
    county: Optional[str] = Query(None),
    prefix: Optional[str] = Query(None),
):
    """Get municipalities, optionally filtered by province and county."""
    return get_municipalities(province=trim_param(province), county=trim_param(county), prefix=trim_param(prefix))


@router.get("/locations/cities")
def get_cities_route(
    province: Optional[str] = Query(None),
    county: Optional[str] = Query(None),
    municipality: Optional[str] = Query(None),
    prefix: Optional[str] = Query(None),
):
    """Get cities, optionally filtered by province, county, and municipality."""
    return get_cities(
        province=trim_param(province),
        county=trim_param(county),
        municipality=trim_param(municipality),
        prefix=trim_param(prefix),
    )


@router.get("/locations/streets")
def get_streets_route(
    city: Optional[str] = Query(None),
    province: Optional[str] = Query(None),
    county: Optional[str] = Query(None),
    municipality: Optional[str] = Query(None),
    prefix: Optional[str] = Query(None),
):
    """Get streets, optionally filtered by city, province, county, and municipality."""
    return get_streets(
        city=trim_param(city),
        province=trim_param(province),
        county=trim_param(county),
        municipality=trim_param(municipality),
        prefix=trim_param(prefix),
    )


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
