from flask import request, jsonify
from postal_service import (
    search_postal_codes,
    get_postal_code_by_code,
    get_provinces,
    get_counties,
    get_municipalities,
    get_cities,
)


def trim_param(value):
    """Trim whitespace from parameter value if it exists"""
    return value.strip() if value else value


def register_routes(app):
    """Register all routes with the Flask app."""

    @app.route("/postal-codes", methods=["GET"])
    def search_postal_codes_route():
        # Get query parameters and trim whitespace
        city = trim_param(request.args.get("city"))
        street = trim_param(request.args.get("street"))
        house_number = trim_param(request.args.get("house_number"))
        province = trim_param(request.args.get("province"))
        county = trim_param(request.args.get("county"))
        municipality = trim_param(request.args.get("municipality"))
        limit = request.args.get("limit", default=100, type=int)

        # Execute search
        response = search_postal_codes(
            city=city,
            street=street,
            house_number=house_number,
            province=province,
            county=county,
            municipality=municipality,
            limit=limit,
        )

        return jsonify(response)

    @app.route("/postal-codes/<postal_code>", methods=["GET"])
    def get_postal_code_route(postal_code):
        result = get_postal_code_by_code(postal_code)

        if not result:
            return jsonify({"error": "Postal code not found"}), 404

        return jsonify(result)

    @app.route("/locations", methods=["GET"])
    def get_locations():
        return jsonify(
            {
                "available_endpoints": {
                    "provinces": "/locations/provinces",
                    "counties": "/locations/counties",
                    "municipalities": "/locations/municipalities",
                    "cities": "/locations/cities",
                }
            }
        )

    @app.route("/locations/provinces", methods=["GET"])
    def get_provinces_route():
        prefix = trim_param(request.args.get("prefix"))
        return jsonify(get_provinces(prefix=prefix))

    @app.route("/locations/counties", methods=["GET"])
    def get_counties_route():
        province = trim_param(request.args.get("province"))
        prefix = trim_param(request.args.get("prefix"))
        return jsonify(get_counties(province=province, prefix=prefix))

    @app.route("/locations/municipalities", methods=["GET"])
    def get_municipalities_route():
        province = trim_param(request.args.get("province"))
        county = trim_param(request.args.get("county"))
        prefix = trim_param(request.args.get("prefix"))
        return jsonify(get_municipalities(province=province, county=county, prefix=prefix))

    @app.route("/locations/cities", methods=["GET"])
    def get_cities_route():
        province = trim_param(request.args.get("province"))
        county = trim_param(request.args.get("county"))
        municipality = trim_param(request.args.get("municipality"))
        prefix = trim_param(request.args.get("prefix"))
        return jsonify(
            get_cities(province=province, county=county, municipality=municipality, prefix=prefix)
        )

    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "healthy"})
