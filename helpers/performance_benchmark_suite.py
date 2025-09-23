#!/usr/bin/env python3
"""
🚀 COMPREHENSIVE PERFORMANCE BENCHMARK SUITE
Advanced performance testing framework for Polish postal code APIs

Features:
- 100+ unique test scenarios with statistical analysis
- Multi-API concurrent testing (Flask, FastAPI, Go, Elixir)
- Real-world usage simulation with fallback testing
- Polish character normalization performance
- Latency percentiles (p50, p75, p90, p95, p99) and statistical measures
- Database-driven test generation from 122k+ postal records
- Advanced reporting with cross-API comparisons

Usage:
    python3 performance_benchmark_suite.py                    # Full benchmark suite
    python3 performance_benchmark_suite.py --api flask        # Test Flask only
    python3 performance_benchmark_suite.py --quick            # Quick performance test
    python3 performance_benchmark_suite.py --warmup 10        # Custom warmup rounds
    python3 performance_benchmark_suite.py --export results   # Export detailed JSON

Created: 2024-09-19 | Optimized for real-world performance insights
"""

import requests
import sqlite3
import json
import time
import argparse
import sys
import random
import statistics
import threading
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple, Any, Union
from enum import Enum
import os


class APIType(Enum):
    FLASK = "flask"
    FASTAPI = "fastapi"
    GO = "go"
    ELIXIR = "elixir"


class TestCategory(Enum):
    EXACT_MATCH = "exact_match"
    FALLBACK_LOGIC = "fallback_logic"
    POLISH_NORMALIZATION = "polish_normalization"
    HUMAN_BEHAVIOR = "human_behavior"
    MULTI_ENDPOINT = "multi_endpoint"


@dataclass
class PerformanceMetrics:
    """Container for performance measurement data"""
    response_times: List[float]
    mean_ms: float
    p50_ms: float
    p75_ms: float
    p90_ms: float
    p95_ms: float
    p99_ms: float
    min_ms: float
    max_ms: float
    std_dev_ms: float
    success_rate: float
    total_requests: int
    failed_requests: int


@dataclass
class TestScenario:
    """Represents a single performance test scenario"""
    id: str
    name: str
    category: TestCategory
    endpoint: str
    params: Dict[str, Any]
    expected_behavior: str
    fallback_expected: bool = False
    normalization_expected: bool = False
    description: str = ""


@dataclass
class APITestResult:
    """Results for a single API test execution"""
    api_name: str
    api_port: int
    scenario: TestScenario
    metrics: PerformanceMetrics
    response_validation: bool
    sample_response: Dict[str, Any]
    error_details: Optional[str] = None


class PolishCharacterNormalizer:
    """Utility for Polish character normalization"""

    POLISH_CHAR_MAP = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
        'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
        'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """Convert Polish characters to ASCII equivalents"""
        if not text:
            return text
        result = text
        for polish_char, ascii_char in cls.POLISH_CHAR_MAP.items():
            result = result.replace(polish_char, ascii_char)
        return result

    @classmethod
    def add_polish_characters(cls, text: str) -> str:
        """Convert some ASCII to Polish characters for testing"""
        conversions = {
            'lodz': 'Łódź', 'krakow': 'Kraków', 'wroclaw': 'Wrocław',
            'gdansk': 'Gdańsk', 'poznan': 'Poznań', 'katowice': 'Katowice'
        }
        text_lower = text.lower()
        for ascii_form, polish_form in conversions.items():
            if ascii_form in text_lower:
                return text.replace(ascii_form, polish_form).replace(ascii_form.title(), polish_form)
        return text


class DatabaseConnection:
    """Manages SQLite database connections for test data generation"""

    def __init__(self, db_path: str = "postal_codes.db"):
        self.db_path = db_path
        self._validate_database()

    def _validate_database(self):
        """Ensure database exists and has expected structure"""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database not found: {self.db_path}")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM postal_codes")
            count = cursor.fetchone()[0]
            if count < 10000:
                raise ValueError(f"Database appears incomplete: only {count} records")

    def execute_query(self, query: str, params: tuple = ()) -> List[tuple]:
        """Execute a database query and return results"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

    def get_random_cities(self, limit: int = 50, by_province: bool = True) -> List[tuple]:
        """Get random cities, optionally distributed across provinces"""
        if by_province:
            query = """
            SELECT DISTINCT city, province, county, municipality
            FROM postal_codes
            WHERE city IS NOT NULL AND province IS NOT NULL
            ORDER BY RANDOM() LIMIT ?
            """
        else:
            query = """
            SELECT DISTINCT city, province, county, municipality
            FROM postal_codes
            WHERE city IS NOT NULL
            ORDER BY RANDOM() LIMIT ?
            """
        return self.execute_query(query, (limit,))

    def get_city_streets(self, city: str, limit: int = 10) -> List[tuple]:
        """Get streets for a specific city"""
        query = """
        SELECT DISTINCT street, house_numbers, postal_code
        FROM postal_codes
        WHERE city LIKE ? AND street IS NOT NULL AND length(street) > 0
        ORDER BY RANDOM() LIMIT ?
        """
        return self.execute_query(query, (f"%{city}%", limit))

    def get_major_cities(self) -> List[tuple]:
        """Get major Polish cities with high record counts"""
        query = """
        SELECT city, COUNT(*) as count, province
        FROM postal_codes
        WHERE city LIKE '%Warszawa%' OR city LIKE '%Kraków%'
           OR city LIKE '%Gdańsk%' OR city LIKE '%Wrocław%'
           OR city LIKE '%Poznań%' OR city LIKE '%Łódź%'
        GROUP BY city
        ORDER BY count DESC
        LIMIT 20
        """
        return self.execute_query(query)

    def get_provinces(self) -> List[str]:
        """Get all Polish provinces"""
        query = "SELECT DISTINCT province FROM postal_codes WHERE province IS NOT NULL"
        return [row[0] for row in self.execute_query(query)]

    def get_sample_postal_codes(self, limit: int = 20) -> List[str]:
        """Get sample postal codes for direct lookup testing"""
        query = "SELECT DISTINCT postal_code FROM postal_codes ORDER BY RANDOM() LIMIT ?"
        return [row[0] for row in self.execute_query(query, (limit,))]


class PerformanceBenchmarkSuite:
    """Main performance testing framework"""

    def __init__(self, warmup_requests: int = 5, test_iterations: int = 20):
        self.warmup_requests = warmup_requests
        self.test_iterations = test_iterations
        self.db = DatabaseConnection()
        self.results: List[APITestResult] = []

        # API configurations
        self.apis = {
            APIType.FLASK: {"name": "Flask", "port": 5001, "base_url": "http://localhost:5001"},
            APIType.FASTAPI: {"name": "FastAPI", "port": 5002, "base_url": "http://localhost:5002"},
            APIType.GO: {"name": "Go", "port": 5003, "base_url": "http://localhost:5003"},
            APIType.ELIXIR: {"name": "Elixir", "port": 5004, "base_url": "http://localhost:5004"}
        }

    def log(self, message: str, level: str = "INFO"):
        """Enhanced logging with timestamps"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def make_http_request(self, base_url: str, endpoint: str, params: Dict[str, Any] = None, timeout: int = 10) -> Tuple[Optional[Dict], float, bool]:
        """Make HTTP request and measure response time"""
        start_time = time.perf_counter()
        try:
            if params:
                query_string = urllib.parse.urlencode(params)
                url = f"{base_url}{endpoint}?{query_string}"
            else:
                url = f"{base_url}{endpoint}"

            response = requests.get(url, timeout=timeout)
            end_time = time.perf_counter()

            response_time_ms = (end_time - start_time) * 1000

            if response.status_code == 200:
                return response.json(), response_time_ms, True
            else:
                return None, response_time_ms, False

        except Exception as e:
            end_time = time.perf_counter()
            response_time_ms = (end_time - start_time) * 1000
            return None, response_time_ms, False

    def calculate_percentiles(self, response_times: List[float]) -> PerformanceMetrics:
        """Calculate comprehensive performance metrics"""
        if not response_times:
            return PerformanceMetrics([], 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, len(response_times))

        sorted_times = sorted(response_times)
        success_count = len([t for t in response_times if t > 0])
        failed_count = len(response_times) - success_count

        # Filter out failed requests (negative times) for percentile calculation
        valid_times = [t for t in response_times if t > 0]

        if not valid_times:
            return PerformanceMetrics(response_times, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, len(response_times), failed_count)

        return PerformanceMetrics(
            response_times=response_times,
            mean_ms=statistics.mean(valid_times),
            p50_ms=statistics.quantiles(valid_times, n=2)[0] if len(valid_times) >= 2 else valid_times[0],
            p75_ms=statistics.quantiles(valid_times, n=4)[2] if len(valid_times) >= 4 else valid_times[-1],
            p90_ms=statistics.quantiles(valid_times, n=10)[8] if len(valid_times) >= 10 else valid_times[-1],
            p95_ms=statistics.quantiles(valid_times, n=20)[18] if len(valid_times) >= 20 else valid_times[-1],
            p99_ms=statistics.quantiles(valid_times, n=100)[98] if len(valid_times) >= 100 else valid_times[-1],
            min_ms=min(valid_times),
            max_ms=max(valid_times),
            std_dev_ms=statistics.stdev(valid_times) if len(valid_times) > 1 else 0,
            success_rate=(success_count / len(response_times)) * 100,
            total_requests=len(response_times),
            failed_requests=failed_count
        )

    def validate_api_availability(self, api_type: APIType) -> bool:
        """Check if API is running and responsive"""
        config = self.apis[api_type]
        try:
            response, _, success = self.make_http_request(config["base_url"], "/health", timeout=5)
            return success
        except:
            return False

    def run_warmup(self, api_type: APIType, scenarios: List[TestScenario]):
        """Run warmup requests to prepare API for testing"""
        config = self.apis[api_type]
        self.log(f"Running {self.warmup_requests} warmup requests for {config['name']}...")

        warmup_scenario = random.choice(scenarios)
        for _ in range(self.warmup_requests):
            self.make_http_request(config["base_url"], warmup_scenario.endpoint, warmup_scenario.params)
            time.sleep(0.1)

    def execute_scenario_performance_test(self, api_type: APIType, scenario: TestScenario) -> APITestResult:
        """Execute performance test for a single scenario"""
        config = self.apis[api_type]
        response_times = []
        sample_response = None
        response_valid = False
        error_details = None

        # Run the test iterations
        for iteration in range(self.test_iterations):
            response, response_time, success = self.make_http_request(
                config["base_url"],
                scenario.endpoint,
                scenario.params
            )

            if success and response:
                response_times.append(response_time)
                if sample_response is None:
                    sample_response = response
                    response_valid = self._validate_response_format(response, scenario)
            else:
                response_times.append(-1)  # Mark failed requests
                if error_details is None:
                    error_details = f"Request failed (iteration {iteration + 1})"

            # Small delay between requests to simulate realistic usage
            time.sleep(0.05)

        metrics = self.calculate_percentiles(response_times)

        return APITestResult(
            api_name=config["name"],
            api_port=config["port"],
            scenario=scenario,
            metrics=metrics,
            response_validation=response_valid,
            sample_response=sample_response or {},
            error_details=error_details
        )

    def _validate_response_format(self, response: Dict, scenario: TestScenario) -> bool:
        """Validate response format matches API specification"""
        if not isinstance(response, dict):
            return False

        # Basic structure validation
        required_fields = ["results", "count"]
        if not all(field in response for field in required_fields):
            return False

        # Results should be a list
        if not isinstance(response.get("results"), list):
            return False

        # Scenario-specific validation
        if scenario.fallback_expected:
            return "fallback_used" in response or "message" in response

        if scenario.normalization_expected:
            return "polish_normalization_used" in response or "search_type" in response

        return True


class TestScenarioGenerator:
    """Generates comprehensive test scenarios for performance testing"""

    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection

    def generate_exact_match_scenarios(self, count: int = 20) -> List[TestScenario]:
        """Generate exact match scenarios with real database data"""
        scenarios = []

        # Get major cities for testing
        major_cities = self.db.get_major_cities()

        for i, (city, record_count, province) in enumerate(major_cities[:10]):
            # Get streets for this city
            streets = self.db.get_city_streets(city, 2)

            for j, (street, house_numbers, postal_code) in enumerate(streets):
                # Generate valid house number for the pattern
                valid_house_number = self._extract_valid_house_number(house_numbers)

                scenario_id = f"exact_match_{i}_{j}"
                scenarios.append(TestScenario(
                    id=scenario_id,
                    name=f"Exact: {city} → {street} #{valid_house_number}",
                    category=TestCategory.EXACT_MATCH,
                    endpoint="/postal-codes",
                    params={
                        "city": city,
                        "street": street,
                        "house_number": str(valid_house_number) if valid_house_number else None
                    },
                    expected_behavior="exact_match",
                    description=f"Exact match for {city}, {street} with house number {valid_house_number}"
                ))

        # Add some city-only exact matches
        random_cities = self.db.get_random_cities(10)
        for i, (city, province, county, municipality) in enumerate(random_cities):
            scenarios.append(TestScenario(
                id=f"exact_city_{i}",
                name=f"Exact: {city} (city-only)",
                category=TestCategory.EXACT_MATCH,
                endpoint="/postal-codes",
                params={"city": city},
                expected_behavior="city_match",
                description=f"City-only exact match for {city}"
            ))

        return scenarios[:count]

    def generate_fallback_scenarios(self, count: int = 25) -> List[TestScenario]:
        """Generate fallback logic test scenarios"""
        scenarios = []

        # House number fallback scenarios
        major_cities = self.db.get_major_cities()
        for i, (city, _, _) in enumerate(major_cities[:8]):
            streets = self.db.get_city_streets(city, 1)
            if streets:
                street, house_numbers, postal_code = streets[0]
                # Use house number that's likely outside the range
                invalid_house_numbers = [999, 1500, 5000, 9999]

                for j, invalid_num in enumerate(invalid_house_numbers[:2]):
                    scenarios.append(TestScenario(
                        id=f"fallback_house_{i}_{j}",
                        name=f"Fallback: {city} → {street} #{invalid_num} (invalid house)",
                        category=TestCategory.FALLBACK_LOGIC,
                        endpoint="/postal-codes",
                        params={
                            "city": city,
                            "street": street,
                            "house_number": str(invalid_num)
                        },
                        expected_behavior="house_number_fallback",
                        fallback_expected=True,
                        description=f"Should fallback from invalid house number {invalid_num} to street-level results"
                    ))

        # Street fallback scenarios
        for i, (city, _, _) in enumerate(major_cities[:8]):
            fake_streets = [
                "Nieistniejąca", "Fałszywa", "Wymyślona", "Błędna",
                "Testowa", "Przykładowa", "Fikcyjna", "Sztuczna"
            ]

            scenarios.append(TestScenario(
                id=f"fallback_street_{i}",
                name=f"Fallback: {city} → {fake_streets[i % len(fake_streets)]} (invalid street)",
                category=TestCategory.FALLBACK_LOGIC,
                endpoint="/postal-codes",
                params={
                    "city": city,
                    "street": fake_streets[i % len(fake_streets)]
                },
                expected_behavior="street_fallback",
                fallback_expected=True,
                description=f"Should fallback from invalid street to city-level results"
            ))

        return scenarios[:count]

    def generate_polish_normalization_scenarios(self, count: int = 20) -> List[TestScenario]:
        """Generate Polish character normalization test scenarios"""
        scenarios = []

        # ASCII → Polish character scenarios
        polish_cities_map = {
            "lodz": "Łódź",
            "krakow": "Kraków",
            "wroclaw": "Wrocław",
            "gdansk": "Gdańsk",
            "poznan": "Poznań",
            "bialystok": "Białystok",
            "czestochowa": "Częstochowa",
            "katowice": "Katowice"
        }

        for i, (ascii_form, polish_form) in enumerate(polish_cities_map.items()):
            scenarios.append(TestScenario(
                id=f"polish_ascii_{i}",
                name=f"Polish: {ascii_form} → {polish_form}",
                category=TestCategory.POLISH_NORMALIZATION,
                endpoint="/postal-codes",
                params={"city": ascii_form},
                expected_behavior="polish_normalization",
                normalization_expected=True,
                description=f"ASCII input '{ascii_form}' should find Polish city '{polish_form}'"
            ))

        # Direct Polish character scenarios
        for i, (_, polish_form) in enumerate(list(polish_cities_map.items())[:6]):
            scenarios.append(TestScenario(
                id=f"polish_direct_{i}",
                name=f"Polish: {polish_form} (direct)",
                category=TestCategory.POLISH_NORMALIZATION,
                endpoint="/postal-codes",
                params={"city": polish_form},
                expected_behavior="direct_polish",
                description=f"Direct Polish character input for '{polish_form}'"
            ))

        # Mixed Polish normalization + fallbacks
        for i, (ascii_form, polish_form) in enumerate(list(polish_cities_map.items())[:6]):
            scenarios.append(TestScenario(
                id=f"polish_fallback_{i}",
                name=f"Polish+Fallback: {ascii_form} → Fake Street",
                category=TestCategory.POLISH_NORMALIZATION,
                endpoint="/postal-codes",
                params={
                    "city": ascii_form,
                    "street": "Nieistniejąca"
                },
                expected_behavior="polish_normalization_fallback",
                normalization_expected=True,
                fallback_expected=True,
                description=f"Polish normalization with street fallback for '{ascii_form}'"
            ))

        return scenarios[:count]

    def generate_human_behavior_scenarios(self, count: int = 25) -> List[TestScenario]:
        """Generate human behavior simulation scenarios"""
        scenarios = []

        # Typos and misspellings
        typo_variations = [
            ("Warszawa", "Warszawa"), ("Warszawaa", "Warszawa"),
            ("Kraków", "Krakow"), ("Krakow", "Kraków"),
            ("Gdańsk", "Gdansk"), ("Gdansk", "Gdańsk"),
            ("Wrocław", "Wroclaw"), ("Poznan", "Poznań")
        ]

        for i, (typo_city, target_city) in enumerate(typo_variations):
            scenarios.append(TestScenario(
                id=f"human_typo_{i}",
                name=f"Human: {typo_city} (typo for {target_city})",
                category=TestCategory.HUMAN_BEHAVIOR,
                endpoint="/postal-codes",
                params={"city": typo_city},
                expected_behavior="typo_handling",
                description=f"Human typo '{typo_city}' should find or fallback gracefully"
            ))

        # Case variations
        case_variations = [
            "WARSZAWA", "warszawa", "WaRsZaWa",
            "KRAKÓW", "kraków", "KrAkÓw",
            "GDAŃSK", "gdańsk", "GdAńSk"
        ]

        for i, variant in enumerate(case_variations):
            scenarios.append(TestScenario(
                id=f"human_case_{i}",
                name=f"Human: {variant} (case variation)",
                category=TestCategory.HUMAN_BEHAVIOR,
                endpoint="/postal-codes",
                params={"city": variant},
                expected_behavior="case_insensitive",
                description=f"Case variation '{variant}' should work"
            ))

        # Partial street names (common human behavior)
        partial_streets = [
            ("Warszawa", "Jerozolimskie"),  # Aleje Jerozolimskie
            ("Kraków", "Główny"),          # Rynek Główny
            ("Gdańsk", "Długa"),           # ul. Długa
            ("Wrocław", "Świdnicka"),      # ul. Świdnicka
            ("Poznań", "Święty Marcin"),   # ul. Święty Marcin
        ]

        for i, (city, partial_street) in enumerate(partial_streets):
            scenarios.append(TestScenario(
                id=f"human_partial_{i}",
                name=f"Human: {city} → {partial_street} (partial street)",
                category=TestCategory.HUMAN_BEHAVIOR,
                endpoint="/postal-codes",
                params={
                    "city": city,
                    "street": partial_street
                },
                expected_behavior="partial_street_match",
                fallback_expected=True,
                description=f"Partial street name '{partial_street}' in {city}"
            ))

        # Spacing and formatting issues
        spacing_issues = [
            ("Warszawa", " Marszałkowska "),  # Extra spaces
            ("Kraków", "al.Mickiewicza"),     # Missing space
            ("Gdańsk", "ul.Długa"),          # Missing space
        ]

        for i, (city, malformed_street) in enumerate(spacing_issues):
            scenarios.append(TestScenario(
                id=f"human_spacing_{i}",
                name=f"Human: {city} → '{malformed_street}' (spacing issue)",
                category=TestCategory.HUMAN_BEHAVIOR,
                endpoint="/postal-codes",
                params={
                    "city": city,
                    "street": malformed_street
                },
                expected_behavior="spacing_tolerance",
                fallback_expected=True,
                description=f"Malformed street with spacing issues"
            ))

        return scenarios[:count]

    def generate_multi_endpoint_scenarios(self, count: int = 10) -> List[TestScenario]:
        """Generate multi-endpoint performance test scenarios"""
        scenarios = []

        # Health check endpoint
        scenarios.append(TestScenario(
            id="endpoint_health",
            name="Health Check",
            category=TestCategory.MULTI_ENDPOINT,
            endpoint="/health",
            params={},
            expected_behavior="health_check",
            description="Health check endpoint performance"
        ))

        # Location hierarchy endpoints
        provinces = self.db.get_provinces()[:5]
        for i, province in enumerate(provinces):
            scenarios.append(TestScenario(
                id=f"endpoint_provinces_{i}",
                name=f"Provinces: {province}",
                category=TestCategory.MULTI_ENDPOINT,
                endpoint="/locations/provinces",
                params={"prefix": province[:3]},
                expected_behavior="location_hierarchy",
                description=f"Province lookup with prefix"
            ))

        # Cities endpoint
        for i in range(3):
            scenarios.append(TestScenario(
                id=f"endpoint_cities_{i}",
                name=f"Cities endpoint #{i+1}",
                category=TestCategory.MULTI_ENDPOINT,
                endpoint="/locations/cities",
                params={"prefix": ["War", "Kra", "Gda"][i]},
                expected_behavior="location_hierarchy",
                description=f"Cities lookup with prefix"
            ))

        # Direct postal code lookup
        postal_codes = self.db.get_sample_postal_codes(5)
        for i, postal_code in enumerate(postal_codes):
            scenarios.append(TestScenario(
                id=f"endpoint_postal_{i}",
                name=f"Direct lookup: {postal_code}",
                category=TestCategory.MULTI_ENDPOINT,
                endpoint=f"/postal-codes/{postal_code}",
                params={},
                expected_behavior="direct_lookup",
                description=f"Direct postal code lookup"
            ))

        return scenarios[:count]

    def _extract_valid_house_number(self, house_pattern: str) -> Optional[int]:
        """Extract a valid house number from a Polish house number pattern"""
        if not house_pattern:
            return None

        try:
            # Handle simple patterns like "1-12", "5-8(n)", "10-15(p)"
            if '-' in house_pattern:
                start_part = house_pattern.split('-')[0]
                # Extract number from start part
                import re
                match = re.search(r'\d+', start_part)
                if match:
                    start_num = int(match.group())
                    # For odd/even patterns, adjust accordingly
                    if '(n)' in house_pattern:  # odd numbers
                        return start_num if start_num % 2 == 1 else start_num + 1
                    elif '(p)' in house_pattern:  # even numbers
                        return start_num if start_num % 2 == 0 else start_num + 1
                    else:
                        return start_num

            # Handle single numbers
            import re
            match = re.search(r'\d+', house_pattern)
            if match:
                return int(match.group())

        except (ValueError, AttributeError):
            pass

        return None

    def generate_all_scenarios(self) -> List[TestScenario]:
        """Generate all test scenarios for comprehensive performance testing"""
        all_scenarios = []

        all_scenarios.extend(self.generate_exact_match_scenarios(20))
        all_scenarios.extend(self.generate_fallback_scenarios(25))
        all_scenarios.extend(self.generate_polish_normalization_scenarios(20))
        all_scenarios.extend(self.generate_human_behavior_scenarios(25))
        all_scenarios.extend(self.generate_multi_endpoint_scenarios(10))

        # Shuffle for more realistic testing patterns
        random.shuffle(all_scenarios)

        return all_scenarios


class BenchmarkReportGenerator:
    """Advanced reporting system for performance benchmark results"""

    def __init__(self):
        self.results: List[APITestResult] = []

    def add_results(self, results: List[APITestResult]):
        """Add test results for report generation"""
        self.results.extend(results)

    def generate_performance_comparison_table(self) -> str:
        """Generate ASCII table comparing API performance"""
        if not self.results:
            return "No results to display"

        # Group results by scenario and API
        scenario_groups = {}
        for result in self.results:
            scenario_id = result.scenario.id
            if scenario_id not in scenario_groups:
                scenario_groups[scenario_id] = {}
            scenario_groups[scenario_id][result.api_name] = result

        output = ["\n🏆 PERFORMANCE COMPARISON TABLE"]
        output.append("=" * 120)
        output.append(f"{'Scenario':<40} {'API':<10} {'Mean':<8} {'p50':<8} {'p90':<8} {'p95':<8} {'p99':<8} {'Success%':<8} {'Status'}")
        output.append("-" * 120)

        for scenario_id, api_results in scenario_groups.items():
            scenario_name = next(iter(api_results.values())).scenario.name[:40]

            # Get all APIs that have results (dynamic list)
            all_api_names = set()
            for result in self.results:
                all_api_names.add(result.api_name)

            # Sort for consistent output
            sorted_api_names = sorted(all_api_names)

            for api_name in sorted_api_names:
                if api_name in api_results:
                    result = api_results[api_name]
                    metrics = result.metrics

                    status = "✅" if metrics.success_rate > 95 else "⚠️" if metrics.success_rate > 80 else "❌"

                    output.append(
                        f"{scenario_name:<40} {api_name:<10} "
                        f"{metrics.mean_ms:<8.1f} {metrics.p50_ms:<8.1f} {metrics.p90_ms:<8.1f} "
                        f"{metrics.p95_ms:<8.1f} {metrics.p99_ms:<8.1f} {metrics.success_rate:<8.1f} {status}"
                    )
                else:
                    output.append(f"{scenario_name:<40} {api_name:<10} {'N/A':<8} {'N/A':<8} {'N/A':<8} {'N/A':<8} {'N/A':<8} {'N/A':<8} ⚫")

            output.append("-" * 120)

        return "\n".join(output)

    def generate_category_summary(self) -> str:
        """Generate performance summary by test category"""
        category_stats = {}

        for result in self.results:
            category = result.scenario.category
            api_name = result.api_name

            if category not in category_stats:
                category_stats[category] = {}
            if api_name not in category_stats[category]:
                category_stats[category][api_name] = []

            category_stats[category][api_name].append(result.metrics)

        output = ["\n📊 CATEGORY PERFORMANCE SUMMARY"]
        output.append("=" * 80)

        for category, api_data in category_stats.items():
            output.append(f"\n🎯 {category.value.upper().replace('_', ' ')}")
            output.append("-" * 50)

            for api_name, metrics_list in api_data.items():
                if metrics_list:
                    avg_mean = sum(m.mean_ms for m in metrics_list) / len(metrics_list)
                    avg_p95 = sum(m.p95_ms for m in metrics_list) / len(metrics_list)
                    avg_success = sum(m.success_rate for m in metrics_list) / len(metrics_list)

                    output.append(f"{api_name:<10}: Mean={avg_mean:<6.1f}ms P95={avg_p95:<6.1f}ms Success={avg_success:<5.1f}%")

        return "\n".join(output)

    def generate_api_winner_analysis(self) -> str:
        """Analyze which API performs best overall"""
        # Get all APIs that have results (dynamic dictionary)
        all_api_names = set()
        for result in self.results:
            all_api_names.add(result.api_name)

        api_scores = {api_name: [] for api_name in all_api_names}

        # Group by scenario for fair comparison
        scenario_groups = {}
        for result in self.results:
            scenario_id = result.scenario.id
            if scenario_id not in scenario_groups:
                scenario_groups[scenario_id] = {}
            scenario_groups[scenario_id][result.api_name] = result

        # Score each API per scenario (lower latency = better score)
        for scenario_id, api_results in scenario_groups.items():
            api_means = {}
            for api_name, result in api_results.items():
                if result.metrics.success_rate > 50:  # Only count successful tests
                    api_means[api_name] = result.metrics.mean_ms

            if len(api_means) >= 2:  # Need at least 2 APIs to compare
                sorted_apis = sorted(api_means.items(), key=lambda x: x[1])
                # Award points: 1st place = 3 points, 2nd = 2 points, 3rd = 1 point
                for i, (api_name, _) in enumerate(sorted_apis):
                    points = max(1, 4 - i - 1)
                    api_scores[api_name].append(points)

        output = ["\n🏅 API PERFORMANCE RANKING"]
        output.append("=" * 60)

        total_scores = {}
        for api_name, scores in api_scores.items():
            if scores:
                total_scores[api_name] = {
                    'total': sum(scores),
                    'avg': sum(scores) / len(scores),
                    'scenarios': len(scores)
                }

        # Sort by total score
        ranked_apis = sorted(total_scores.items(), key=lambda x: x[1]['total'], reverse=True)

        for i, (api_name, stats) in enumerate(ranked_apis):
            rank_emoji = ["🥇", "🥈", "🥉"][i] if i < 3 else f"{i+1}."
            output.append(f"{rank_emoji} {api_name}: {stats['total']} points (avg {stats['avg']:.1f}, {stats['scenarios']} scenarios)")

        return "\n".join(output)

    def export_detailed_json(self, filename: str = "performance_results.json") -> str:
        """Export detailed results to JSON file"""
        export_data = {
            "benchmark_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_scenarios": len(set(r.scenario.id for r in self.results)),
            "total_apis_tested": len(set(r.api_name for r in self.results)),
            "results": []
        }

        for result in self.results:
            export_data["results"].append({
                "scenario": asdict(result.scenario),
                "api_name": result.api_name,
                "api_port": result.api_port,
                "metrics": asdict(result.metrics),
                "response_validation": result.response_validation,
                "sample_response": result.sample_response,
                "error_details": result.error_details
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return f"Detailed results exported to {filename}"


class ConcurrentBenchmarkRunner:
    """Handles concurrent testing across multiple APIs"""

    def __init__(self, suite: PerformanceBenchmarkSuite):
        self.suite = suite
        self.report_generator = BenchmarkReportGenerator()

    def run_concurrent_api_tests(self, scenarios: List[TestScenario], selected_apis: List[APIType] = None) -> List[APITestResult]:
        """Run tests concurrently across multiple APIs"""
        if selected_apis is None:
            selected_apis = [APIType.FLASK, APIType.FASTAPI, APIType.GO, APIType.ELIXIR]

        # Check API availability first
        available_apis = []
        for api_type in selected_apis:
            if self.suite.validate_api_availability(api_type):
                available_apis.append(api_type)
                self.suite.log(f"✅ {self.suite.apis[api_type]['name']} API is available on port {self.suite.apis[api_type]['port']}")
            else:
                self.suite.log(f"❌ {self.suite.apis[api_type]['name']} API is not available on port {self.suite.apis[api_type]['port']}")

        if not available_apis:
            self.suite.log("ERROR: No APIs are available for testing")
            return []

        all_results = []

        # Run warmup for all available APIs
        self.suite.log(f"\n🔥 WARMUP PHASE")
        for api_type in available_apis:
            self.suite.run_warmup(api_type, scenarios)

        self.suite.log(f"\n🚀 PERFORMANCE TESTING PHASE")
        self.suite.log(f"Testing {len(scenarios)} scenarios across {len(available_apis)} APIs")
        self.suite.log(f"Each scenario will run {self.suite.test_iterations} iterations")

        with ThreadPoolExecutor(max_workers=len(available_apis)) as executor:
            # Submit all API+scenario combinations
            future_to_info = {}

            for scenario in scenarios:
                for api_type in available_apis:
                    future = executor.submit(self.suite.execute_scenario_performance_test, api_type, scenario)
                    future_to_info[future] = (api_type, scenario)

            # Collect results as they complete
            completed = 0
            total_tests = len(scenarios) * len(available_apis)

            for future in as_completed(future_to_info):
                api_type, scenario = future_to_info[future]
                try:
                    result = future.result()
                    all_results.append(result)
                    completed += 1

                    # Progress reporting
                    progress = (completed / total_tests) * 100
                    self.suite.log(f"Progress: {progress:.1f}% - Completed {scenario.name} on {result.api_name}")

                except Exception as e:
                    self.suite.log(f"ERROR: Failed to test {scenario.name} on {self.suite.apis[api_type]['name']}: {e}")

        return all_results

    def run_full_benchmark(self, quick_mode: bool = False) -> str:
        """Run complete benchmark suite with reporting"""
        # Generate test scenarios
        generator = TestScenarioGenerator(self.suite.db)

        if quick_mode:
            scenarios = []
            scenarios.extend(generator.generate_exact_match_scenarios(5))
            scenarios.extend(generator.generate_fallback_scenarios(5))
            scenarios.extend(generator.generate_polish_normalization_scenarios(5))
            scenarios.extend(generator.generate_human_behavior_scenarios(5))
            scenarios.extend(generator.generate_multi_endpoint_scenarios(3))
            self.suite.log("🏃 QUICK MODE: Running abbreviated test suite")
        else:
            scenarios = generator.generate_all_scenarios()
            self.suite.log("🏃 FULL MODE: Running comprehensive test suite")

        self.suite.log(f"Generated {len(scenarios)} test scenarios")

        # Run concurrent tests
        results = self.run_concurrent_api_tests(scenarios)

        if not results:
            return "No test results to report"

        # Generate reports
        self.report_generator.add_results(results)

        report_output = []
        report_output.append(f"\n🎯 PERFORMANCE BENCHMARK RESULTS")
        report_output.append(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        report_output.append(f"Total Scenarios: {len(scenarios)}")
        report_output.append(f"Total Results: {len(results)}")
        report_output.append(f"Test Iterations per Scenario: {self.suite.test_iterations}")

        report_output.append(self.report_generator.generate_performance_comparison_table())
        report_output.append(self.report_generator.generate_category_summary())
        report_output.append(self.report_generator.generate_api_winner_analysis())

        return "\n".join(report_output)


# Main execution with command-line interface
def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(description="🚀 Comprehensive Performance Benchmark Suite for Polish Postal Code APIs")

    parser.add_argument("--api", choices=["flask", "fastapi", "go", "elixir"], help="Test specific API only")
    parser.add_argument("--quick", action="store_true", help="Run quick test suite (reduced scenarios)")
    parser.add_argument("--iterations", type=int, default=20, help="Number of test iterations per scenario (default: 20)")
    parser.add_argument("--warmup", type=int, default=5, help="Number of warmup requests (default: 5)")
    parser.add_argument("--export", type=str, help="Export detailed results to JSON file")
    parser.add_argument("--port", type=int, help="Test API on specific port")

    args = parser.parse_args()

    # Initialize benchmark suite
    suite = PerformanceBenchmarkSuite(
        warmup_requests=args.warmup,
        test_iterations=args.iterations
    )

    runner = ConcurrentBenchmarkRunner(suite)

    # Determine which APIs to test
    selected_apis = []
    if args.api:
        api_map = {"flask": APIType.FLASK, "fastapi": APIType.FASTAPI, "go": APIType.GO, "elixir": APIType.ELIXIR}
        selected_apis = [api_map[args.api]]
    elif args.port:
        # Find API by port
        for api_type, config in suite.apis.items():
            if config["port"] == args.port:
                selected_apis = [api_type]
                break
        if not selected_apis:
            print(f"ERROR: No API configured for port {args.port}")
            sys.exit(1)

    # Run benchmark
    try:
        if selected_apis:
            generator = TestScenarioGenerator(suite.db)
            scenarios = generator.generate_all_scenarios()
            if args.quick:
                scenarios = scenarios[:23]  # Reduced set for quick testing

            results = runner.run_concurrent_api_tests(scenarios, selected_apis)
            runner.report_generator.add_results(results)

            print(runner.report_generator.generate_performance_comparison_table())
            print(runner.report_generator.generate_category_summary())

        else:
            # Full benchmark across all APIs
            report = runner.run_full_benchmark(args.quick)
            print(report)

        # Export results if requested
        if args.export:
            export_msg = runner.report_generator.export_detailed_json(args.export)
            print(f"\n📄 {export_msg}")

    except KeyboardInterrupt:
        print("\n⚠️  Benchmark interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()