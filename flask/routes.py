from flask import request, jsonify
from postal_service import (
    search_postal_codes,
    get_postal_code_by_code,
    get_provinces,
    get_counties,
    get_municipalities,
    get_cities
)

def register_routes(app):
    """Register all routes with the Flask app."""

    @app.route('/postal-codes', methods=['GET'])
    def search_postal_codes_route():
        # Get query parameters
        city = request.args.get('city')
        street = request.args.get('street')
        house_number = request.args.get('house_number')
        province = request.args.get('province')
        county = request.args.get('county')
        municipality = request.args.get('municipality')
        limit = request.args.get('limit', default=100, type=int)

        # Execute search
        response = search_postal_codes(
            city=city,
            street=street,
            house_number=house_number,
            province=province,
            county=county,
            municipality=municipality,
            limit=limit
        )

        return jsonify(response)

    @app.route('/postal-codes/<postal_code>', methods=['GET'])
    def get_postal_code_route(postal_code):
        result = get_postal_code_by_code(postal_code)

        if not result:
            return jsonify({'error': 'Postal code not found'}), 404

        return jsonify(result)

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
    def get_provinces_route():
        return jsonify(get_provinces())

    @app.route('/locations/counties', methods=['GET'])
    def get_counties_route():
        province = request.args.get('province')
        return jsonify(get_counties(province=province))

    @app.route('/locations/municipalities', methods=['GET'])
    def get_municipalities_route():
        province = request.args.get('province')
        county = request.args.get('county')
        return jsonify(get_municipalities(province=province, county=county))

    @app.route('/locations/cities', methods=['GET'])
    def get_cities_route():
        province = request.args.get('province')
        county = request.args.get('county')
        municipality = request.args.get('municipality')
        return jsonify(get_cities(province=province, county=county, municipality=municipality))

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({'status': 'healthy'})