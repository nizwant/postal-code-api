#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE POSTAL CODE API TEST SUITE - ALL-IN-ONE

The ultimate testing solution for Polish postal code APIs.
Tests complete pipeline from CSV → Database → API responses.
Includes human behavior simulation, Polish character handling, and cross-API validation.

✨ Features:
- ✅ Postal code verification with exact matches
- ✅ Random CSV-based test generation from 117k records
- ✅ Polish character normalization testing (ASCII ↔ Polish)
- ✅ House number pattern validation (odd/even, DK ranges, etc.)
- ✅ Geographic diversity testing (all provinces)
- ✅ Performance benchmarking
- ✅ Cross-API consistency validation

Usage:
    python3 comprehensive_postal_test_suite.py                    # Test all APIs (full suite)
    python3 comprehensive_postal_test_suite.py --api flask        # Test Flask only
    python3 comprehensive_postal_test_suite.py --port 5003        # Test API on port 5003
    python3 comprehensive_postal_test_suite.py --quick            # Core + random CSV tests
    python3 comprehensive_postal_test_suite.py --polish-tests     # Polish character tests
    python3 comprehensive_postal_test_suite.py --random-csv-tests # Random CSV verification
    python3 comprehensive_postal_test_suite.py --save-results     # Save detailed JSON

Created: 2024-09-19 | Enhanced with postal code verification
"""

import requests
import urllib.parse
import json
import time
import argparse
import sys
import csv
import random
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


class TestCategory(Enum):
    CORE = "core"              # Must pass - pipeline integrity
    HUMAN = "human"            # May fail - real user behavior
    EDGE = "edge"              # Should handle gracefully
    PERFORMANCE = "performance" # Benchmarks


class TestStatus(Enum):
    PASS = "✅"
    FAIL = "❌"
    WARN = "⚠️"
    INFO = "ℹ️"


@dataclass
class TestResult:
    name: str
    category: TestCategory
    status: TestStatus
    expected: Any
    actual: Any
    response_time_ms: float
    details: str
    critical: bool = True  # Whether failure should cause overall failure


class PolishCharacterNormalizer:
    """Utility for handling Polish character normalization"""

    POLISH_CHAR_MAP = {
        'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
        'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
        'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
        'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
    }

    @classmethod
    def normalize_text(cls, text):
        """Convert Polish characters to ASCII equivalents."""
        if not text:
            return text

        result = text
        for polish_char, ascii_char in cls.POLISH_CHAR_MAP.items():
            result = result.replace(polish_char, ascii_char)
        return result


class HouseNumberPatternExtractor:
    """Utility for extracting valid house numbers from Polish address patterns"""

    @staticmethod
    def extract_simple_house_number(house_pattern):
        """Extract a valid house number from a pattern for testing."""
        if not house_pattern:
            return None

        # Handle simple ranges like "1-12"
        if re.match(r'^\d+-\d+$', house_pattern):
            start, end = map(int, house_pattern.split('-'))
            return str(random.randint(start, min(end, start + 10)))

        # Handle odd patterns like "1-19(n)"
        if re.match(r'^\d+-\d+\(n\)$', house_pattern):
            match = re.match(r'^(\d+)-(\d+)\(n\)$', house_pattern)
            start, end = int(match.group(1)), int(match.group(2))
            # Generate odd number in range
            for num in range(start, min(end + 1, start + 20), 2):
                if num % 2 == 1:
                    return str(num)

        # Handle even patterns like "2-16(p)"
        if re.match(r'^\d+-\d+\(p\)$', house_pattern):
            match = re.match(r'^(\d+)-(\d+)\(p\)$', house_pattern)
            start, end = int(match.group(1)), int(match.group(2))
            # Generate even number in range
            for num in range(start, min(end + 1, start + 20), 2):
                if num % 2 == 0:
                    return str(num)

        # Handle individual numbers
        if re.match(r'^\d+$', house_pattern):
            return house_pattern

        # Handle DK patterns like "19-DK"
        if 'DK' in house_pattern:
            match = re.match(r'^(\d+)-DK', house_pattern)
            if match:
                start = int(match.group(1))
                return str(start + random.randint(0, 10))

        return None


class CSVTestGenerator:
    """Generates test cases from CSV data"""

    def __init__(self, csv_path: str = 'postal_codes_poland.csv'):
        self.csv_path = csv_path
        self.records = []
        self.load_csv_data()

    def load_csv_data(self):
        """Load CSV data if available"""
        if not os.path.exists(self.csv_path):
            print(f"Warning: {self.csv_path} not found. CSV-based tests will be limited.")
            return

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.records = list(reader)
            print(f"Loaded {len(self.records)} records from {self.csv_path}")
        except Exception as e:
            print(f"Error loading CSV: {e}")

    def generate_polish_character_tests(self):
        """Generate tests for Polish character handling with postal code verification."""
        if not self.records:
            return []

        test_cases = []

        # Filter for records with Polish characters in city names
        polish_cities = {}
        for record in self.records:
            city = record['Miejscowość']
            if any(char in city for char in 'ąćęłńóśźżĄĆĘŁŃÓŚŹŻ'):
                ascii_city = PolishCharacterNormalizer.normalize_text(city)
                if ascii_city not in polish_cities:
                    polish_cities[ascii_city] = []
                polish_cities[ascii_city].append(record)

        # Łódź specific tests with known postal codes
        lodz_records = [r for r in self.records if 'Łódź' in r['Miejscowość']]

        # City-only Łódź tests
        lodz_city_records = [r for r in lodz_records if not r['Ulica']]
        if lodz_city_records:
            sample_record = random.choice(lodz_city_records)
            test_cases.extend([
                {
                    'name': 'Polish ASCII: "lodz" city → finds Łódź',
                    'params': {'city': 'lodz', 'limit': '5'},
                    'expected_postal_codes': [sample_record['PNA']],
                    'expected_city_contains': 'Łódź',
                    'critical': False,
                    'search_type': 'polish_normalization'
                },
                {
                    'name': 'Polish ASCII: "Lodz" city → finds Łódź',
                    'params': {'city': 'Lodz', 'limit': '5'},
                    'expected_postal_codes': [sample_record['PNA']],
                    'expected_city_contains': 'Łódź',
                    'critical': False,
                    'search_type': 'polish_normalization'
                }
            ])

        # Łódź with street tests
        lodz_brzezinska = [r for r in lodz_records if 'Brzezińska' in r.get('Ulica', '')]
        if lodz_brzezinska:
            record = lodz_brzezinska[0]
            test_cases.extend([
                {
                    'name': 'Polish ASCII: "lodz" + "brzezinska" → finds Łódź Brzezińska',
                    'params': {'city': 'lodz', 'street': 'brzezinska', 'limit': '3'},
                    'expected_postal_codes': [record['PNA']],
                    'expected_city_contains': 'Łódź',
                    'expected_street_contains': 'Brzezińska',
                    'critical': False,
                    'search_type': 'polish_normalization'
                },
                {
                    'name': 'Polish ASCII: "lodz" + "Brzezinska" + house → finds exact address',
                    'params': {'city': 'lodz', 'street': 'brzezinska', 'house_number': '1', 'limit': '3'},
                    'expected_postal_codes': [record['PNA']],
                    'expected_city_contains': 'Łódź',
                    'expected_street_contains': 'Brzezińska',
                    'critical': False,
                    'search_type': 'polish_normalization'
                }
            ])

        # Other Polish cities (sample first 5)
        for ascii_city, city_records in list(polish_cities.items())[:5]:
            original_city = city_records[0]['Miejscowość']
            if 'Łódź' in original_city:
                continue

            city_only_records = [r for r in city_records if not r['Ulica']]
            if city_only_records:
                sample_record = random.choice(city_only_records)
                test_cases.append({
                    'name': f'Polish ASCII: "{ascii_city.lower()}" → finds {original_city}',
                    'params': {'city': ascii_city.lower(), 'limit': '3'},
                    'expected_postal_codes': [sample_record['PNA']],
                    'expected_city_contains': original_city.split('(')[0].strip(),
                    'critical': False,
                    'search_type': 'polish_normalization'
                })

        return test_cases

    def generate_random_csv_tests(self, num_tests=15):
        """Generate random test cases from CSV data."""
        if not self.records:
            return []

        test_cases = []

        # City-only tests
        city_only_records = [r for r in self.records if not r['Ulica']]
        for i in range(min(num_tests // 3, len(city_only_records))):
            record = random.choice(city_only_records)
            test_cases.append({
                'name': f'Random CSV: City "{record["Miejscowość"]}" → {record["PNA"]}',
                'params': {'city': record['Miejscowość']},
                'expected_postal_codes': [record['PNA']],
                'expected_province': record['Województwo'],
                'expected_county': record['Powiat'],
                'critical': True,
                'search_type': 'exact_match'
            })

        # City + street tests
        city_street_records = [r for r in self.records if r['Ulica'] and not r['Numery']]
        for i in range(min(num_tests // 3, len(city_street_records))):
            record = random.choice(city_street_records)
            test_cases.append({
                'name': f'Random CSV: "{record["Miejscowość"]}" + "{record["Ulica"]}" → {record["PNA"]}',
                'params': {'city': record['Miejscowość'], 'street': record['Ulica']},
                'expected_postal_codes': [record['PNA']],
                'expected_province': record['Województwo'],
                'critical': True,
                'search_type': 'exact_match'
            })

        # Full address tests
        full_address_records = [r for r in self.records if r['Ulica'] and r['Numery']]
        for i in range(min(num_tests // 3, len(full_address_records))):
            record = random.choice(full_address_records)
            house_num = HouseNumberPatternExtractor.extract_simple_house_number(record['Numery'])

            if house_num:
                test_cases.append({
                    'name': f'Random CSV: Full address "{record["Miejscowość"]}" + "{record["Ulica"]}" + {house_num} → {record["PNA"]}',
                    'params': {
                        'city': record['Miejscowość'],
                        'street': record['Ulica'],
                        'house_number': house_num
                    },
                    'expected_postal_codes': [record['PNA']],
                    'expected_province': record['Województwo'],
                    'house_pattern': record['Numery'],
                    'critical': True,
                    'search_type': 'house_number_pattern'
                })

        return test_cases


class ComprehensivePostalAPITestSuite:
    """Comprehensive test suite for postal code APIs with all features included"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.apis = {
            'flask': 'http://localhost:5001',
            'fastapi': 'http://localhost:5002'
        }
        self.csv_generator = CSVTestGenerator()

    def log(self, message: str, level: str = "INFO"):
        """Log message if verbose mode is on"""
        if self.verbose:
            timestamp = time.strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")

    def make_request(self, base_url: str, endpoint: str, params: Dict = None) -> Tuple[Optional[Dict], float]:
        """Make API request and return result + response time"""
        start_time = time.time()

        try:
            if params:
                param_strings = []
                for key, value in params.items():
                    if value is not None:
                        encoded_value = urllib.parse.quote(str(value))
                        param_strings.append(f"{key}={encoded_value}")

                url = f"{base_url}{endpoint}"
                if param_strings:
                    url += "?" + "&".join(param_strings)
            else:
                url = f"{base_url}{endpoint}"

            response = requests.get(url, timeout=10)
            response.raise_for_status()
            result = response.json()

            response_time = (time.time() - start_time) * 1000
            return result, response_time

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log(f"Request failed: {e}")
            return None, response_time

    def validate_postal_code_result(self, result: Dict, test: Dict) -> Tuple[TestStatus, str]:
        """Validate API result against expected postal code and other criteria"""
        if not result or 'results' not in result or not result['results']:
            return TestStatus.FAIL, "No results returned"

        results = result['results']

        # Check expected postal codes
        if 'expected_postal_codes' in test:
            found_codes = [r.get('postal_code') for r in results]
            expected_codes = test['expected_postal_codes']

            if not any(code in found_codes for code in expected_codes):
                return TestStatus.FAIL, f"Expected postal codes {expected_codes}, got {found_codes[:3]}..."

        # Check city contains expected text
        if 'expected_city_contains' in test:
            cities = [r.get('city', '') for r in results]
            expected_city_text = test['expected_city_contains']

            if not any(expected_city_text in city for city in cities):
                return TestStatus.FAIL, f"Expected city containing '{expected_city_text}', got {cities[:3]}..."

        # Check street contains expected text
        if 'expected_street_contains' in test:
            streets = [r.get('street', '') for r in results]
            expected_street_text = test['expected_street_contains']

            if not any(expected_street_text in street for street in streets):
                return TestStatus.FAIL, f"Expected street containing '{expected_street_text}', got {streets[:3]}..."

        # Check province
        if 'expected_province' in test:
            provinces = [r.get('province', '') for r in results]
            expected_province = test['expected_province']

            if expected_province not in provinces:
                return TestStatus.FAIL, f"Expected province '{expected_province}', got {provinces[:3]}..."

        # Check minimum count
        if 'min_count' in test and len(results) < test['min_count']:
            return TestStatus.FAIL, f"Expected at least {test['min_count']} results, got {len(results)}"

        return TestStatus.PASS, f"Found {len(results)} valid results"

    def run_core_validation_tests(self, api_name: str, base_url: str):
        """Essential tests that must pass for API to be considered functional"""

        self.log(f"\n🔍 CORE VALIDATION TESTS - {api_name}")
        self.log("=" * 60)

        core_tests = [
            # Health check
            {
                'name': 'API Health Check',
                'endpoint': '/health',
                'params': None,
                'validator': lambda result: result and result.get('status') == 'healthy'
            },

            # Warsaw house number patterns (verified from CSV)
            {
                'name': 'Warsaw House 5 (odd pattern 1-19(n))',
                'endpoint': '/postal-codes',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Edwarda Józefa Abramowskiego',
                    'house_number': '5'
                },
                'expected_codes': ['02-659']
            },

            {
                'name': 'Warsaw House 6 (even pattern 2-16a(p))',
                'endpoint': '/postal-codes',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Edwarda Józefa Abramowskiego',
                    'house_number': '6'
                },
                'expected_codes': ['02-659']
            },

            {
                'name': 'Warsaw House 25 (DK pattern 21-DK(n))',
                'endpoint': '/postal-codes',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Edwarda Józefa Abramowskiego',
                    'house_number': '25'
                },
                'expected_codes': ['02-669']
            },

            # Łódź complex slash notation
            {
                'name': 'Łódź Complex Slash Pattern (1/3-23/25(n))',
                'endpoint': '/postal-codes',
                'params': {
                    'city': 'Łódź',
                    'street': 'Brzezińska',
                    'house_number': '1'
                },
                'expected_codes': ['92-103']
            },

            # DK (open-ended) ranges
            {
                'name': 'DK Open-ended Range (19-DK)',
                'endpoint': '/postal-codes',
                'params': {
                    'city': 'Antoninów',
                    'house_number': '100'
                },
                'expected_codes': ['09-500']
            }
        ]

        for test in core_tests:
            if 'validator' in test:
                # Custom validation (like health check)
                result, response_time = self.make_request(base_url, test['endpoint'], test.get('params'))

                if result and test['validator'](result):
                    test_result = TestResult(
                        name=f"[{api_name}] {test['name']}",
                        category=TestCategory.CORE,
                        status=TestStatus.PASS,
                        expected="Valid response",
                        actual=str(result),
                        response_time_ms=response_time,
                        details="Health check passed",
                        critical=True
                    )
                else:
                    test_result = TestResult(
                        name=f"[{api_name}] {test['name']}",
                        category=TestCategory.CORE,
                        status=TestStatus.FAIL,
                        expected="Valid response",
                        actual=str(result),
                        response_time_ms=response_time,
                        details="Health check failed",
                        critical=True
                    )
            else:
                # Expected postal code validation
                result, response_time = self.make_request(base_url, test['endpoint'], test['params'])

                if result and 'results' in result and result['results']:
                    found_codes = [r.get('postal_code') for r in result['results']]
                    expected_codes = test['expected_codes']

                    if any(code in found_codes for code in expected_codes):
                        test_result = TestResult(
                            name=f"[{api_name}] {test['name']}",
                            category=TestCategory.CORE,
                            status=TestStatus.PASS,
                            expected=str(expected_codes),
                            actual=str(found_codes[:3]),
                            response_time_ms=response_time,
                            details=f"Found expected postal code(s)",
                            critical=True
                        )
                    else:
                        test_result = TestResult(
                            name=f"[{api_name}] {test['name']}",
                            category=TestCategory.CORE,
                            status=TestStatus.FAIL,
                            expected=str(expected_codes),
                            actual=str(found_codes[:3]),
                            response_time_ms=response_time,
                            details=f"Expected codes {expected_codes}, got {found_codes[:3]}",
                            critical=True
                        )
                else:
                    test_result = TestResult(
                        name=f"[{api_name}] {test['name']}",
                        category=TestCategory.CORE,
                        status=TestStatus.FAIL,
                        expected=str(test['expected_codes']),
                        actual="No results",
                        response_time_ms=response_time,
                        details="No results returned",
                        critical=True
                    )

            self.results.append(test_result)
            print(f"{test_result.status.value} {test_result.name} ({test_result.response_time_ms:.1f}ms)")

    def run_enhanced_polish_tests(self, api_name: str, base_url: str):
        """Run enhanced Polish character tests with postal code verification"""

        self.log(f"\n🇵🇱 ENHANCED POLISH CHARACTER TESTS - {api_name}")
        self.log("=" * 60)

        # Generate Polish character tests from CSV
        polish_tests = self.csv_generator.generate_polish_character_tests()

        if not polish_tests:
            self.log("No CSV data available for Polish character tests, using defaults")
            polish_tests = [
                {
                    'name': 'Polish ASCII: "lodz" city → finds Łódź',
                    'params': {'city': 'lodz', 'limit': '5'},
                    'expected_city_contains': 'Łódź',
                    'critical': False,
                    'min_count': 1
                }
            ]

        for test in polish_tests:
            result, response_time = self.make_request(base_url, '/postal-codes', test['params'])

            status, details = self.validate_postal_code_result(result, test)

            test_result = TestResult(
                name=f"[{api_name}] {test['name']}",
                category=TestCategory.HUMAN,
                status=status,
                expected=str(test.get('expected_postal_codes', test.get('expected_city_contains', 'Valid results'))),
                actual=str([r.get('postal_code', 'N/A') for r in result.get('results', [])][:3]) if result else "No results",
                response_time_ms=response_time,
                details=details,
                critical=test.get('critical', False)
            )

            self.results.append(test_result)
            print(f"{test_result.status.value} {test_result.name} ({test_result.response_time_ms:.1f}ms)")

    def run_random_csv_tests(self, api_name: str, base_url: str):
        """Run random CSV-based tests with exact postal code verification"""

        self.log(f"\n🎲 RANDOM CSV VALIDATION TESTS - {api_name}")
        self.log("=" * 60)

        # Generate random CSV tests
        csv_tests = self.csv_generator.generate_random_csv_tests(15)

        if not csv_tests:
            self.log("No CSV data available for random tests")
            return

        for test in csv_tests:
            result, response_time = self.make_request(base_url, '/postal-codes', test['params'])

            status, details = self.validate_postal_code_result(result, test)

            test_result = TestResult(
                name=f"[{api_name}] {test['name']}",
                category=TestCategory.CORE,
                status=status,
                expected=str(test.get('expected_postal_codes', ['N/A'])),
                actual=str([r.get('postal_code', 'N/A') for r in result.get('results', [])][:3]) if result else "No results",
                response_time_ms=response_time,
                details=details,
                critical=test.get('critical', True)
            )

            self.results.append(test_result)
            print(f"{test_result.status.value} {test_result.name} ({test_result.response_time_ms:.1f}ms)")

    def run_human_behavior_tests(self, api_name: str, base_url: str):
        """Test how API handles real human search patterns"""

        self.log(f"\n👤 HUMAN BEHAVIOR TESTS - {api_name}")
        self.log("=" * 60)
        self.log("These tests simulate real user behavior. Some failures are expected.")

        human_tests = [
            {
                'name': 'Human: Partial Street "Abramow" → finds "Abramowskiego"',
                'params': {'city': 'Warszawa', 'street': 'Abramow', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },
            {
                'name': 'Human: ASCII "Bialystok" → finds "Białystok"',
                'params': {'city': 'Bialystok', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },
            {
                'name': 'Human: Lowercase "warszawa" (case insensitive)',
                'params': {'city': 'warszawa', 'limit': '3'},
                'min_count': 1,
                'critical': False
            }
        ]

        for test in human_tests:
            result, response_time = self.make_request(base_url, '/postal-codes', test['params'])

            if result and 'results' in result and len(result['results']) >= test.get('min_count', 1):
                status = TestStatus.PASS
                details = f"Found {len(result['results'])} results"
            else:
                status = TestStatus.FAIL if test['critical'] else TestStatus.WARN
                details = f"Expected at least {test.get('min_count', 1)} results, got {len(result.get('results', []))}"

            test_result = TestResult(
                name=f"[{api_name}] {test['name']}",
                category=TestCategory.HUMAN,
                status=status,
                expected=f"≥{test.get('min_count', 1)} results",
                actual=f"{len(result.get('results', []))} results" if result else "No results",
                response_time_ms=response_time,
                details=details,
                critical=test['critical']
            )

            self.results.append(test_result)
            print(f"{test_result.status.value} {test_result.name} ({test_result.response_time_ms:.1f}ms)")

    def run_edge_case_tests(self, api_name: str, base_url: str):
        """Test edge cases and error handling"""

        self.log(f"\n⚠️  EDGE CASE TESTS - {api_name}")
        self.log("=" * 60)

        edge_tests = [
            {
                'name': 'Edge: Empty City',
                'params': {'city': '', 'street': 'Test'},
                'should_fail': True,
                'critical': False
            },
            {
                'name': 'Edge: Non-existent City',
                'params': {'city': 'NonExistentCity123'},
                'should_fail': True,
                'critical': False
            },
            {
                'name': 'Edge: Number Outside Range',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Edwarda Józefa Abramowskiego',
                    'house_number': '200'  # Outside known ranges
                },
                'should_fail': True,
                'critical': False
            }
        ]

        for test in edge_tests:
            result, response_time = self.make_request(base_url, '/postal-codes', test['params'])

            should_fail = test.get('should_fail', False)
            has_results = result and 'results' in result and len(result['results']) > 0

            if should_fail:
                status = TestStatus.PASS if not has_results else TestStatus.WARN
                details = "Correctly returned no results" if not has_results else f"Unexpectedly found {len(result['results'])} results"
            else:
                status = TestStatus.PASS if has_results else TestStatus.FAIL
                details = f"Found {len(result['results'])} results" if has_results else "No results found"

            test_result = TestResult(
                name=f"[{api_name}] {test['name']}",
                category=TestCategory.EDGE,
                status=status,
                expected="No results" if should_fail else "Some results",
                actual=f"{len(result.get('results', []))} results" if result else "No results",
                response_time_ms=response_time,
                details=details,
                critical=test['critical']
            )

            self.results.append(test_result)
            print(f"{test_result.status.value} {test_result.name} ({test_result.response_time_ms:.1f}ms)")

    def run_performance_tests(self, api_name: str, base_url: str):
        """Test performance benchmarks"""

        self.log(f"\n📈 PERFORMANCE TESTS - {api_name}")
        self.log("=" * 60)

        perf_tests = [
            {
                'name': 'Perf: Simple Lookup',
                'params': {'city': 'Abisynia'},
                'max_time_ms': 100
            },
            {
                'name': 'Perf: Complex Pattern',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Edwarda Józefa Abramowskiego',
                    'house_number': '5'
                },
                'max_time_ms': 200
            },
            {
                'name': 'Perf: City Search with Limit',
                'params': {'city': 'Warszawa', 'limit': '10'},
                'max_time_ms': 300
            }
        ]

        for test in perf_tests:
            result, response_time = self.make_request(base_url, '/postal-codes', test['params'])

            max_time = test['max_time_ms']
            if response_time <= max_time:
                status = TestStatus.PASS
                details = f"Response time {response_time:.1f}ms ≤ {max_time}ms"
            else:
                status = TestStatus.WARN
                details = f"Response time {response_time:.1f}ms > {max_time}ms (slow)"

            test_result = TestResult(
                name=f"[{api_name}] {test['name']}",
                category=TestCategory.PERFORMANCE,
                status=status,
                expected=f"≤{max_time}ms",
                actual=f"{response_time:.1f}ms",
                response_time_ms=response_time,
                details=details,
                critical=False
            )

            self.results.append(test_result)
            print(f"{test_result.status.value} {test_result.name} ({test_result.response_time_ms:.1f}ms)")

    def compare_apis(self, apis: Dict[str, str]):
        """Compare consistency between different API implementations"""

        self.log(f"\n🔄 CROSS-API CONSISTENCY TESTS")
        self.log("=" * 60)

        test_queries = [
            {'city': 'Warszawa', 'street': 'Edwarda Józefa Abramowskiego', 'house_number': '5'},
            {'city': 'Łódź', 'street': 'Brzezińska', 'house_number': '1'},
            {'city': 'Białystok', 'limit': '5'}
        ]

        for i, query in enumerate(test_queries):
            results_by_api = {}

            for api_name, base_url in apis.items():
                result, response_time = self.make_request(base_url, '/postal-codes', query)
                if result and 'results' in result:
                    # Normalize results for comparison
                    postal_codes = sorted([r.get('postal_code') for r in result['results']])
                    results_by_api[api_name] = postal_codes

            # Compare results
            if len(set(str(codes) for codes in results_by_api.values())) == 1:
                status = TestStatus.PASS
                details = "All APIs returned identical results"
            else:
                status = TestStatus.WARN
                details = f"APIs returned different results: {results_by_api}"

            test_result = TestResult(
                name=f"Cross-API Consistency Test {i+1}",
                category=TestCategory.CORE,
                status=status,
                expected="Identical results across APIs",
                actual=str(results_by_api),
                response_time_ms=0,
                details=details,
                critical=False
            )

            self.results.append(test_result)
            print(f"{test_result.status.value} {test_result.name}")

    def print_summary(self) -> bool:
        """Print test summary and return success status"""

        print(f"\n{'='*80}")
        print("📊 TEST SUMMARY")
        print(f"{'='*80}")

        # Count by category and status
        by_category = {}
        by_status = {}
        critical_failures = 0

        for result in self.results:
            # By category
            if result.category not in by_category:
                by_category[result.category] = {'total': 0, 'passed': 0, 'failed': 0}
            by_category[result.category]['total'] += 1
            if result.status == TestStatus.PASS:
                by_category[result.category]['passed'] += 1
            else:
                by_category[result.category]['failed'] += 1

            # By status
            if result.status not in by_status:
                by_status[result.status] = 0
            by_status[result.status] += 1

            # Critical failures
            if result.critical and result.status == TestStatus.FAIL:
                critical_failures += 1

        # Print category breakdown
        for category, stats in by_category.items():
            pass_rate = (stats['passed'] / stats['total']) * 100 if stats['total'] > 0 else 0
            print(f"{category.value.upper():12} | {stats['passed']:3}/{stats['total']:3} passed ({pass_rate:5.1f}%)")

        print(f"\n{'Total Results:'}")
        for status, count in by_status.items():
            print(f"  {status.value} {count}")

        # Overall status
        total_tests = len(self.results)
        passed_tests = by_status.get(TestStatus.PASS, 0)
        pass_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

        print(f"\n📈 Overall: {passed_tests}/{total_tests} passed ({pass_rate:.1f}%)")

        if critical_failures > 0:
            print(f"❌ {critical_failures} critical failures detected")
            return False
        elif pass_rate >= 80:
            print("✅ Test suite passed!")
            return True
        else:
            print("⚠️  Test suite completed with warnings")
            return False

    def save_results(self, filename: str = None):
        """Save detailed results to JSON file"""
        if filename is None:
            filename = f"test_results_{time.strftime('%Y%m%d_%H%M%S')}.json"

        # Convert results to JSON-serializable format
        json_results = []
        for result in self.results:
            json_results.append({
                'name': result.name,
                'category': result.category.value,
                'status': result.status.value,
                'expected': result.expected,
                'actual': result.actual,
                'response_time_ms': result.response_time_ms,
                'details': result.details,
                'critical': result.critical
            })

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_tests': len(self.results),
                'results': json_results
            }, f, indent=2, ensure_ascii=False)

        print(f"💾 Results saved to {filename}")


def main():
    """Main test runner"""

    parser = argparse.ArgumentParser(
        description='Comprehensive Postal Code API Test Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 comprehensive_postal_test_suite.py                    # Test all APIs (full suite)
  python3 comprehensive_postal_test_suite.py --api flask        # Test Flask only
  python3 comprehensive_postal_test_suite.py --port 5003        # Test API on port 5003
  python3 comprehensive_postal_test_suite.py --quick            # Core + random CSV tests
  python3 comprehensive_postal_test_suite.py --polish-tests     # Enhanced Polish character tests
  python3 comprehensive_postal_test_suite.py --random-csv-tests # Random CSV tests with postal code verification
  python3 comprehensive_postal_test_suite.py --human-tests      # Human behavior tests
  python3 comprehensive_postal_test_suite.py --save-results     # Save JSON results
        """
    )

    parser.add_argument('--api', choices=['flask', 'fastapi'], help='Test specific API only')
    parser.add_argument('--port', type=int, help='Test API on specific port')
    parser.add_argument('--host', default='localhost', help='API host (default: localhost)')
    parser.add_argument('--quick', action='store_true', help='Run only core validation tests + random CSV tests')
    parser.add_argument('--human-tests', action='store_true', help='Run only human behavior tests')
    parser.add_argument('--csv-tests', action='store_true', help='Run only CSV validation tests')
    parser.add_argument('--polish-tests', action='store_true', help='Run only enhanced Polish character tests')
    parser.add_argument('--random-csv-tests', action='store_true', help='Run only random CSV tests with postal code verification')
    parser.add_argument('--save-results', action='store_true', help='Save detailed JSON results')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')

    args = parser.parse_args()

    # Initialize test suite
    suite = ComprehensivePostalAPITestSuite(verbose=not args.quiet)

    # Determine which APIs to test
    if args.port:
        apis = {f'port_{args.port}': f'http://{args.host}:{args.port}'}
    elif args.api:
        if args.api == 'flask':
            apis = {'flask': f'http://{args.host}:5001'}
        else:
            apis = {'fastapi': f'http://{args.host}:5002'}
    else:
        apis = {
            'flask': f'http://{args.host}:5001',
            'fastapi': f'http://{args.host}:5002'
        }

    # Run tests
    print("🚀 COMPREHENSIVE POSTAL CODE API TEST SUITE")
    print("=" * 80)
    print(f"Testing {len(apis)} API(s): {', '.join(apis.keys())}")

    for api_name, base_url in apis.items():
        print(f"\n🎯 Testing {api_name.upper()} at {base_url}")
        print("-" * 60)

        if args.human_tests:
            suite.run_human_behavior_tests(api_name, base_url)
        elif args.polish_tests:
            suite.run_enhanced_polish_tests(api_name, base_url)
        elif args.random_csv_tests:
            suite.run_random_csv_tests(api_name, base_url)
        elif args.quick:
            suite.run_core_validation_tests(api_name, base_url)
            suite.run_random_csv_tests(api_name, base_url)
        else:
            # Full test suite
            suite.run_core_validation_tests(api_name, base_url)
            suite.run_random_csv_tests(api_name, base_url)
            suite.run_enhanced_polish_tests(api_name, base_url)
            suite.run_human_behavior_tests(api_name, base_url)
            suite.run_edge_case_tests(api_name, base_url)
            suite.run_performance_tests(api_name, base_url)

    # Cross-API comparison if multiple APIs
    if len(apis) > 1 and not args.human_tests:
        suite.compare_apis(apis)

    # Print summary
    success = suite.print_summary()

    # Save results if requested
    if args.save_results:
        suite.save_results()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()