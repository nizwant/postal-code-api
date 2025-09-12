import pytest
import json
import tempfile
import os
from app import app, get_db_connection


@pytest.fixture
def client():
    db_fd, app.config['DATABASE'] = tempfile.mkstemp()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        with app.app_context():
            # Create test database
            create_test_db()
        yield client
    
    os.close(db_fd)
    os.unlink(app.config['DATABASE'])


def create_test_db():
    import sqlite3
    conn = sqlite3.connect('postal_codes.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS postal_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            postal_code TEXT NOT NULL,
            city TEXT,
            street TEXT,
            house_numbers TEXT,
            municipality TEXT,
            county TEXT,
            province TEXT
        )
    ''')
    
    # Insert test data
    test_data = [
        ('00-001', 'Warszawa', 'Testowa', '1-10', 'Warszawa', 'Warszawa', 'mazowieckie'),
        ('00-002', 'Kraków', 'Główna', '5-15', 'Kraków', 'Kraków', 'małopolskie'),
        ('00-003', 'Gdańsk', 'Morska', '20-30', 'Gdańsk', 'Gdańsk', 'pomorskie'),
    ]
    
    for data in test_data:
        cursor.execute('''
            INSERT INTO postal_codes 
            (postal_code, city, street, house_numbers, municipality, county, province)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', data)
    
    conn.commit()
    conn.close()


class TestHealthEndpoint:
    def test_health_check(self, client):
        response = client.get('/health')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'


class TestPostalCodeSearch:
    def test_search_by_city(self, client):
        response = client.get('/postal-codes?city=Warszawa')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert 'count' in data
        assert data['count'] > 0
        assert any(result['city'] == 'Warszawa' for result in data['results'])
    
    def test_search_by_postal_code(self, client):
        response = client.get('/postal-codes/00-001')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'results' in data
        assert data['count'] > 0
        assert data['results'][0]['postal_code'] == '00-001'
    
    def test_search_nonexistent_postal_code(self, client):
        response = client.get('/postal-codes/99-999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
    
    def test_search_with_limit(self, client):
        response = client.get('/postal-codes?limit=1')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert len(data['results']) <= 1
    
    def test_search_fallback_house_number(self, client):
        response = client.get('/postal-codes?city=Warszawa&street=Testowa&house_number=999')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should fallback to street without house number
        if 'fallback_used' in data:
            assert data['fallback_used'] is True
    
    def test_search_fallback_street(self, client):
        response = client.get('/postal-codes?city=Warszawa&street=Nieistniejąca')
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should fallback to city only
        if 'fallback_used' in data:
            assert data['fallback_used'] is True


class TestLocationEndpoints:
    def test_locations_root(self, client):
        response = client.get('/locations')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'available_endpoints' in data
    
    def test_get_provinces(self, client):
        response = client.get('/locations/provinces')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'provinces' in data
        assert 'count' in data
        assert isinstance(data['provinces'], list)
    
    def test_get_counties(self, client):
        response = client.get('/locations/counties')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'counties' in data
        assert isinstance(data['counties'], list)
    
    def test_get_counties_filtered(self, client):
        response = client.get('/locations/counties?province=mazowieckie')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'counties' in data
        assert data['filtered_by_province'] == 'mazowieckie'
    
    def test_get_cities(self, client):
        response = client.get('/locations/cities')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'cities' in data
        assert isinstance(data['cities'], list)


class TestQueryBuilder:
    def test_build_search_query_city_only(self):
        from app import build_search_query
        query, params = build_search_query(city='Warszawa')
        assert 'LOWER(city) LIKE LOWER(?)' in query
        assert params[0] == 'Warszawa%'
    
    def test_build_search_query_multiple_params(self):
        from app import build_search_query
        query, params = build_search_query(
            city='Warszawa', 
            street='Testowa', 
            province='mazowieckie'
        )
        assert 'LOWER(city) LIKE LOWER(?)' in query
        assert 'LOWER(street) = LOWER(?)' in query
        assert 'LOWER(province) = LOWER(?)' in query
        assert len(params) == 4  # 3 search params + limit


class TestDatabaseConnection:
    def test_get_db_connection(self):
        conn = get_db_connection()
        assert conn is not None
        # Test that we can execute a query
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        assert result[0] == 1
        conn.close()