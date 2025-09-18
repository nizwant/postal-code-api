#!/usr/bin/env python3
"""
🎯 COMPREHENSIVE POSTAL CODE API TEST SUITE

The ultimate testing solution for Polish postal code APIs.
Tests complete pipeline from CSV → Database → API responses.
Includes human behavior simulation and cross-API validation.

Usage:
    python3 postal_api_test_suite.py                    # Test all APIs (full suite)
    python3 postal_api_test_suite.py --api flask        # Test Flask only
    python3 postal_api_test_suite.py --port 5003        # Test API on port 5003 (e.g., Go)
    python3 postal_api_test_suite.py --quick            # Run only core tests
    python3 postal_api_test_suite.py --csv-tests        # Run only CSV validation tests
    python3 postal_api_test_suite.py --human-tests      # Run only human behavior tests
    python3 postal_api_test_suite.py --save-results     # Save detailed JSON results

Created from comprehensive validation performed on 2025-09-15
"""

import requests
import urllib.parse
import json
import time
import argparse
import sys
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


class PostalAPITestSuite:
    """Comprehensive test suite for postal code APIs"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.apis = {
            'flask': 'http://localhost:5001',
            'fastapi': 'http://localhost:5002'
        }

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
                # Build URL with properly encoded parameters
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

            response_time = (time.time() - start_time) * 1000  # Convert to ms
            return result, response_time

        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            self.log(f"Request error: {e}", "ERROR")
            return None, response_time

    def run_test(self,
                 name: str,
                 category: TestCategory,
                 api_name: str,
                 base_url: str,
                 endpoint: str,
                 params: Dict = None,
                 expected_codes: List[str] = None,
                 expected_count: int = None,
                 min_count: int = None,
                 should_fail: bool = False,
                 critical: bool = True) -> TestResult:
        """Run a single test and return result"""

        result, response_time = self.make_request(base_url, endpoint, params)

        if result is None:
            return TestResult(
                name=f"[{api_name}] {name}",
                category=category,
                status=TestStatus.FAIL,
                expected="Valid response",
                actual="Request failed",
                response_time_ms=response_time,
                details="Network/API error",
                critical=critical
            )

        # Analyze result
        count = result.get('count', 0)
        postal_codes = [r.get('postal_code') for r in result.get('results', [])]

        # Determine test outcome
        status = TestStatus.PASS
        details = f"{count} results: {postal_codes[:3]}{'...' if len(postal_codes) > 3 else ''}"

        # Check expectations
        if should_fail:
            if count > 0:
                status = TestStatus.WARN
                details = f"Expected no results but got {count}"
        elif expected_codes:
            if set(postal_codes) != set(expected_codes):
                status = TestStatus.FAIL if critical else TestStatus.WARN
                details = f"Expected {expected_codes}, got {postal_codes}"
        elif expected_count is not None:
            if count != expected_count:
                status = TestStatus.FAIL if critical else TestStatus.WARN
                details = f"Expected {expected_count} results, got {count}"
        elif min_count is not None:
            if count < min_count:
                status = TestStatus.WARN
                details = f"Expected at least {min_count} results, got {count}"

        return TestResult(
            name=f"[{api_name}] {name}",
            category=category,
            status=status,
            expected=expected_codes or expected_count or min_count or "Success",
            actual=postal_codes or count,
            response_time_ms=response_time,
            details=details,
            critical=critical
        )

    def run_core_validation_tests(self, api_name: str, base_url: str):
        """Run core validation tests - these MUST pass for API to be considered working"""

        self.log(f"\n🔍 CORE VALIDATION TESTS - {api_name}")
        self.log("=" * 60)

        core_tests = [
            # Health check
            {
                'name': 'Health Check',
                'endpoint': '/health',
                'params': None,
                'validator': lambda r: r and r.get('status') == 'healthy'
            },

            # Core pipeline integrity tests
            {
                'name': 'Rural Village - Abisynia',
                'endpoint': '/postal-codes',
                'params': {'city': 'Abisynia'},
                'expected_codes': ['83-440']
            },

            # Warsaw complex house number patterns (from original CSV validation)
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

            # Białystok letter suffixes
            {
                'name': 'Białystok Letter Range (6a-6c)',
                'endpoint': '/postal-codes',
                'params': {
                    'city': 'Białystok',
                    'street': 'Władysława Broniewskiego',
                    'house_number': '6b'
                },
                'expected_codes': ['15-730']
            },

            {
                'name': 'Białystok Individual Letter (24a)',
                'endpoint': '/postal-codes',
                'params': {
                    'city': 'Białystok',
                    'street': 'M. Curie-Skłodowskiej',
                    'house_number': '24a'
                },
                'min_count': 1  # Should find at least one result, may match multiple patterns
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
                # Standard postal code test
                test_result = self.run_test(
                    name=test['name'],
                    category=TestCategory.CORE,
                    api_name=api_name,
                    base_url=base_url,
                    endpoint=test['endpoint'],
                    params=test['params'],
                    expected_codes=test.get('expected_codes'),
                    min_count=test.get('min_count'),
                    critical=True
                )

            self.results.append(test_result)
            print(f"{test_result.status.value} {test_result.name} ({test_result.response_time_ms:.1f}ms)")
            if test_result.status != TestStatus.PASS:
                print(f"    {test_result.details}")

    def run_human_behavior_tests(self, api_name: str, base_url: str):
        """Test how API handles real human search patterns - these may fail and that's OK"""

        self.log(f"\n👤 HUMAN BEHAVIOR TESTS - {api_name}")
        self.log("=" * 60)
        self.log("These tests simulate real user behavior. Some failures are expected.")

        human_tests = [
            # Partial street names (what humans actually type)
            {
                'name': 'Human: Partial Street "Broniewskiego"',
                'params': {'city': 'Białystok', 'street': 'Broniewskiego', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },

            {
                'name': 'Human: Short Name "Curie"',
                'params': {'city': 'Białystok', 'street': 'Curie', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },

            {
                'name': 'Human: Warsaw Partial "Abramowskiego"',
                'params': {'city': 'Warszawa', 'street': 'Abramowskiego', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },

            # Case sensitivity tests
            {
                'name': 'Human: Lowercase Street "broniewskiego"',
                'params': {'city': 'Białystok', 'street': 'broniewskiego', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },

            {
                'name': 'Human: Uppercase Street "BRONIEWSKIEGO"',
                'params': {'city': 'Białystok', 'street': 'BRONIEWSKIEGO', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },

            {
                'name': 'Human: Lowercase City "warszawa"',
                'params': {'city': 'warszawa', 'street': 'Abramowskiego', 'limit': '3'},
                'min_count': 1,
                'critical': False  # This will likely fail - city names are case sensitive
            },

            # Polish character variations (now should work with two-tier search)
            {
                'name': 'Human: ASCII "Lodz" → finds "Łódź"',
                'params': {'city': 'Lodz', 'limit': '3'},
                'min_count': 1,
                'critical': False  # Now should pass with Polish character fallback
            },

            {
                'name': 'Human: ASCII "Bialystok" → finds "Białystok"',
                'params': {'city': 'Bialystok', 'street': 'Broniewskiego', 'limit': '3'},
                'min_count': 1,
                'critical': False  # Now should pass with Polish character fallback
            },

            # Street-level Polish character normalization tests
            {
                'name': 'Human: ASCII "zlota" → finds "Złota" street in Warsaw',
                'params': {'city': 'Warszawa', 'street': 'zlota', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters',
                'validator': lambda result: (
                    result.get('search_type') == 'polish_characters' and
                    any('Złota' in str(r.get('street', '')) for r in result.get('results', []))
                )
            },

            {
                'name': 'Human: ASCII "Lodz" variations → finds "Łódź"',
                'params': {'city': 'Lodz', 'limit': '5'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },

            {
                'name': 'Human: Mixed case "lodz" → finds Polish cities',
                'params': {'city': 'lodz', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },

            {
                'name': 'Human: ASCII "bialystok" → finds "Białystok"',
                'params': {'city': 'bialystok', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },

            {
                'name': 'Human: ASCII street "brzezinska" → finds "Brzezińska"',
                'params': {'city': 'Lodz', 'street': 'brzezinska', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },

            # Comprehensive Łódź variations test coverage
            # Test 1: łodz (lowercase ł with ASCII o, z)
            {
                'name': 'Polish: "łodz" city only → finds Łódź',
                'params': {'city': 'łodz', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },
            {
                'name': 'Polish: "łodz" with street → finds Łódź + street',
                'params': {'city': 'łodz', 'street': 'Brzezińska', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },
            {
                'name': 'Polish: "łodz" with street+house → finds Łódź address',
                'params': {'city': 'łodz', 'street': 'Brzezińska', 'house_number': '1', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },

            # Test 2: lódź (ASCII l with Polish ó, ź)
            {
                'name': 'Polish: "lódź" city only → finds Łódź',
                'params': {'city': 'lódź', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },
            {
                'name': 'Polish: "lódź" with street → finds Łódź + street',
                'params': {'city': 'lódź', 'street': 'Brzezińska', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },
            {
                'name': 'Polish: "lódź" with street+house → finds Łódź address',
                'params': {'city': 'lódź', 'street': 'Brzezińska', 'house_number': '1', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },

            # Test 3: łódź (full Polish characters)
            {
                'name': 'Polish: "łódź" city only → exact or normalized match',
                'params': {'city': 'łódź', 'limit': '3'},
                'min_count': 1,
                'critical': False
                # Note: This might be 'exact' if database has this form
            },
            {
                'name': 'Polish: "łódź" with street → exact or normalized match',
                'params': {'city': 'łódź', 'street': 'Brzezińska', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },
            {
                'name': 'Polish: "łódź" with street+house → exact or normalized address',
                'params': {'city': 'łódź', 'street': 'Brzezińska', 'house_number': '1', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },

            # Test 4: Mixed ASCII/Polish street combinations
            {
                'name': 'Polish: ASCII city "lodz" + ASCII street "brzezinska"',
                'params': {'city': 'lodz', 'street': 'brzezinska', 'limit': '3'},
                'min_count': 1,
                'critical': False,
                'expected_search_type': 'polish_characters'
            },
            {
                'name': 'Polish: Polish city "łódź" + ASCII street "brzezinska"',
                'params': {'city': 'łódź', 'street': 'brzezinska', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },
            {
                'name': 'Polish: ASCII city "lodz" + Polish street "Brzezińska"',
                'params': {'city': 'lodz', 'street': 'Brzezińska', 'limit': '3'},
                'min_count': 1,
                'critical': False
            },

            # Common typos and approximations
            {
                'name': 'Human: Close Typo "Broniewski" (missing "ego")',
                'params': {'city': 'Białystok', 'street': 'Broniewski', 'limit': '3'},
                'min_count': 1,
                'critical': False  # This will likely fail
            },

            # Extra spaces (should work)
            {
                'name': 'Human: Extra Spaces " Warszawa "',
                'params': {'city': ' Warszawa ', 'street': '  Abramowskiego  ', 'limit': '3'},
                'min_count': 1,
                'critical': False
            }
        ]

        for test in human_tests:
            # Handle tests with custom validators
            if 'validator' in test:
                result, response_time = self.make_request(base_url, '/postal-codes', test['params'])

                if result and test['validator'](result):
                    test_result = TestResult(
                        name=f"[{api_name}] {test['name']}",
                        category=TestCategory.HUMAN,
                        status=TestStatus.PASS,
                        expected="Custom validation passed",
                        actual=f"search_type: {result.get('search_type', 'unknown')}",
                        response_time_ms=response_time,
                        details=f"Found {result.get('count', 0)} results with correct Polish normalization",
                        critical=test['critical']
                    )
                else:
                    test_result = TestResult(
                        name=f"[{api_name}] {test['name']}",
                        category=TestCategory.HUMAN,
                        status=TestStatus.WARN if not test['critical'] else TestStatus.FAIL,
                        expected="Custom validation passed",
                        actual=f"search_type: {result.get('search_type', 'unknown') if result else 'no response'}",
                        response_time_ms=response_time,
                        details="Custom validation failed - check Polish character normalization",
                        critical=test['critical']
                    )
            else:
                test_result = self.run_test(
                    name=test['name'],
                    category=TestCategory.HUMAN,
                    api_name=api_name,
                    base_url=base_url,
                    endpoint='/postal-codes',
                    params=test['params'],
                    min_count=test.get('min_count'),
                    critical=test['critical']
                )

            self.results.append(test_result)
            print(f"{test_result.status.value} {test_result.name} ({test_result.response_time_ms:.1f}ms)")
            if test_result.status == TestStatus.WARN or test_result.status == TestStatus.FAIL:
                print(f"    {test_result.details}")

    def run_edge_case_tests(self, api_name: str, base_url: str):
        """Test edge cases and boundary conditions"""

        self.log(f"\n⚠️  EDGE CASE TESTS - {api_name}")
        self.log("=" * 60)

        edge_tests = [
            # House number constraints
            {
                'name': 'Edge: Even Number in Odd Range (house 4 in 1-19(n))',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Edwarda Józefa Abramowskiego',
                    'house_number': '4'
                },
                'should_fail': True,
                'critical': False
            },

            {
                'name': 'Edge: Odd Number in Even Range (house 7 in 2-16a(p))',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Edwarda Józefa Abramowskiego',
                    'house_number': '7'
                },
                'should_fail': True,
                'critical': False
            },

            {
                'name': 'Edge: Number Outside Range (house 20 > 1-19(n))',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Edwarda Józefa Abramowskiego',
                    'house_number': '20'
                },
                'should_fail': True,
                'critical': False
            },

            {
                'name': 'Edge: Number Below DK Range (house 18 < 19-DK)',
                'params': {
                    'city': 'Antoninów',
                    'house_number': '18'
                },
                'should_fail': True,
                'critical': False
            },

            # Invalid inputs
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
            }
        ]

        for test in edge_tests:
            test_result = self.run_test(
                name=test['name'],
                category=TestCategory.EDGE,
                api_name=api_name,
                base_url=base_url,
                endpoint='/postal-codes',
                params=test['params'],
                should_fail=test.get('should_fail', False),
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
            test_result = self.run_test(
                name=test['name'],
                category=TestCategory.PERFORMANCE,
                api_name=api_name,
                base_url=base_url,
                endpoint='/postal-codes',
                params=test['params'],
                critical=False
            )

            # Check performance
            if test_result.response_time_ms > test['max_time_ms']:
                test_result.status = TestStatus.WARN
                test_result.details += f" (SLOW: >{test['max_time_ms']}ms)"

            self.results.append(test_result)
            print(f"{test_result.status.value} {test_result.name} ({test_result.response_time_ms:.1f}ms)")

    def run_csv_validation_tests(self, api_name: str, base_url: str):
        """Test that API outputs match original CSV data"""

        self.log(f"\n📊 CSV VALIDATION TESTS - {api_name}")
        self.log("=" * 60)
        self.log("Testing diverse examples from original CSV data")

        # Diverse examples collected from CSV analysis
        csv_validation_tests = [
            # Village entries (no streets)
            {
                'name': 'CSV: Village Abisynia (83-440)',
                'params': {'city': 'Abisynia'},
                'expected_postal_code': '83-440',
                'expected_province': 'pomorskie',
                'expected_county': 'kościerski'
            },
            {
                'name': 'CSV: Village Abramy (05-310)',
                'params': {'city': 'Abramy'},
                'expected_postal_code': '05-310',
                'expected_province': 'mazowieckie',
                'expected_county': 'miński'
            },

            # Complex Warsaw addresses with house number patterns
            {
                'name': 'CSV: Warsaw Aleja 3 Maja 1 (odd)',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Aleja 3 Maja',
                    'house_number': '1'
                },
                'expected_postal_code': '00-401',
                'expected_house_pattern': '1-DK(n)'
            },
            {
                'name': 'CSV: Warsaw Aleja 3 Maja 2 (even)',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Aleja 3 Maja',
                    'house_number': '2'
                },
                'expected_postal_code': '00-391',
                'expected_house_pattern': '2-12(p)'
            },
            {
                'name': 'CSV: Warsaw Aleja 3 Maja 14 (even)',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Aleja 3 Maja',
                    'house_number': '14'
                },
                'expected_postal_code': '00-381',
                'expected_house_pattern': '14-DK(p)'
            },
            {
                'name': 'CSV: Warsaw Abramowskiego 5 (odd)',
                'params': {
                    'city': 'Warszawa',
                    'street': 'Edwarda Józefa Abramowskiego',
                    'house_number': '5'
                },
                'expected_postal_code': '02-659',
                'expected_house_pattern': '1-19(n), 2-16a(p)'
            },

            # Gdansk examples with different patterns
            {
                'name': 'CSV: Gdansk Arkońska 25',
                'params': {
                    'city': 'Gdańsk',
                    'street': 'Arkońska',
                    'house_number': '25'
                },
                'expected_postal_code': '80-387',
                'expected_house_pattern': '5-29a'
            },
            {
                'name': 'CSV: Gdansk Arkońska 30 (DK range)',
                'params': {
                    'city': 'Gdańsk',
                    'street': 'Arkońska',
                    'house_number': '30'
                },
                'expected_postal_code': '80-392',
                'expected_house_pattern': '30-DK'
            },

            # Białystok examples with complex patterns
            {
                'name': 'CSV: Bialystok Pilsudskiego 1 (odd)',
                'params': {
                    'city': 'Białystok',
                    'street': 'Aleja Józefa Piłsudskiego',
                    'house_number': '1'
                },
                'expected_postal_code': '15-443',
                'expected_house_pattern': '1-11(n)'
            },
            {
                'name': 'CSV: Bialystok Pilsudskiego 44 (even DK)',
                'params': {
                    'city': 'Białystok',
                    'street': 'Aleja Józefa Piłsudskiego',
                    'house_number': '44'
                },
                'expected_postal_code': '15-088',
                'expected_house_pattern': '44-DK(p)'
            },

            # Będzin with complex comma-separated patterns
            {
                'name': 'CSV: Bedzin Swierczewskiego 17 (odd)',
                'params': {
                    'city': 'Będzin',
                    'street': 'Karola Świerczewskiego',
                    'house_number': '17'
                },
                'expected_postal_code': '42-500',
                'expected_house_pattern': '2-15, 17-103(n), 28-102(p), 115'
            },
            {
                'name': 'CSV: Bedzin Swierczewskiego 28 (even)',
                'params': {
                    'city': 'Będzin',
                    'street': 'Karola Świerczewskiego',
                    'house_number': '28'
                },
                'expected_postal_code': '42-500',
                'expected_house_pattern': '2-15, 17-103(n), 28-102(p), 115'
            },

            # Rural examples with unique provinces
            {
                'name': 'CSV: Bialka Tatrzanska (mountain village)',
                'params': {
                    'city': 'Białka Tatrzańska',
                    'street': 'Środkowa',
                    'house_number': '10'
                },
                'expected_postal_code': '34-405',
                'expected_province': 'małopolskie',
                'expected_county': 'tatrzański'
            },

            # Multiple cities with same name (different provinces)
            {
                'name': 'CSV: Adamowo (mazowieckie - Czerwonka)',
                'params': {'city': 'Adamowo', 'municipality': 'Czerwonka'},
                'expected_postal_code': '06-232',
                'expected_province': 'mazowieckie',
                'expected_county': 'makowski'
            },
            {
                'name': 'CSV: Adamowo (warmińsko-mazurskie - Elbląg)',
                'params': {'city': 'Adamowo', 'municipality': 'Elbląg'},
                'expected_postal_code': '82-300',
                'expected_province': 'warmińsko-mazurskie',
                'expected_county': 'elbląski'
            }
        ]

        for test in csv_validation_tests:
            result, response_time = self.make_request(base_url, '/postal-codes', test['params'])

            if result and 'results' in result and len(result['results']) > 0:
                first_result = result['results'][0]
                status = TestStatus.PASS
                details = f"Found {len(result['results'])} records"

                # Validate postal code if specified
                if 'expected_postal_code' in test:
                    if first_result.get('postal_code') != test['expected_postal_code']:
                        status = TestStatus.FAIL
                        details = f"Expected postal code {test['expected_postal_code']}, got {first_result.get('postal_code')}"

                # Validate province if specified
                if 'expected_province' in test and status == TestStatus.PASS:
                    if first_result.get('province') != test['expected_province']:
                        status = TestStatus.FAIL
                        details = f"Expected province {test['expected_province']}, got {first_result.get('province')}"

                # Validate county if specified
                if 'expected_county' in test and status == TestStatus.PASS:
                    if first_result.get('county') != test['expected_county']:
                        status = TestStatus.FAIL
                        details = f"Expected county {test['expected_county']}, got {first_result.get('county')}"

                # Note house pattern for reference (not validation since patterns are complex)
                if 'expected_house_pattern' in test and status == TestStatus.PASS:
                    details += f" | Pattern: {test['expected_house_pattern']}"

            else:
                status = TestStatus.FAIL
                details = "No results found"
                first_result = None

            test_result = TestResult(
                name=test['name'],
                category=TestCategory.CORE,  # CSV validation is core functionality
                status=status,
                expected=test.get('expected_postal_code', 'data found'),
                actual=first_result.get('postal_code') if first_result else 'none',
                response_time_ms=response_time,
                details=details,
                critical=True
            )

            self.results.append(test_result)
            print(f"{test_result.status.value} [{api_name}] {test_result.name} ({test_result.response_time_ms:.1f}ms)")
            if test_result.status == TestStatus.FAIL:
                print(f"    {test_result.details}")

    def compare_apis(self, apis: Dict[str, str]):
        """Compare multiple APIs for consistency"""

        if len(apis) < 2:
            return

        self.log(f"\n🔄 CROSS-API CONSISTENCY CHECK")
        self.log("=" * 60)

        # Test case that should return identical results
        test_params = {
            'city': 'Warszawa',
            'street': 'Edwarda Józefa Abramowskiego',
            'house_number': '5'
        }

        results = {}
        for api_name, base_url in apis.items():
            result, response_time = self.make_request(base_url, '/postal-codes', test_params)
            if result:
                postal_codes = [r.get('postal_code') for r in result.get('results', [])]
                results[api_name] = postal_codes
            else:
                results[api_name] = "ERROR"

        print(f"Test: Warsaw Edwarda Józefa Abramowskiego, house 5")
        print(f"Expected: ['02-659']")
        print()

        consistent = True
        reference_result = None

        for api_name, result in results.items():
            print(f"{api_name:12}: {result}")
            if reference_result is None:
                reference_result = result
            elif result != reference_result:
                consistent = False

        if consistent and reference_result == ['02-659']:
            print("\n✅ All APIs return consistent and correct results!")
            consistency_result = TestResult(
                name="Cross-API Consistency",
                category=TestCategory.CORE,
                status=TestStatus.PASS,
                expected="Identical results",
                actual="All APIs consistent",
                response_time_ms=0,
                details="APIs return identical results",
                critical=True
            )
        else:
            print("\n❌ APIs return different results - investigation needed!")
            consistency_result = TestResult(
                name="Cross-API Consistency",
                category=TestCategory.CORE,
                status=TestStatus.FAIL,
                expected="Identical results",
                actual=str(results),
                response_time_ms=0,
                details="APIs return different results",
                critical=True
            )

        self.results.append(consistency_result)

    def print_summary(self):
        """Print comprehensive test summary"""

        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)

        # Group results by category
        categories = {cat: [] for cat in TestCategory}
        for result in self.results:
            categories[result.category].append(result)

        total_tests = len(self.results)
        total_passed = sum(1 for r in self.results if r.status == TestStatus.PASS)
        total_failed = sum(1 for r in self.results if r.status == TestStatus.FAIL)
        total_warnings = sum(1 for r in self.results if r.status == TestStatus.WARN)

        critical_failed = sum(1 for r in self.results if r.status == TestStatus.FAIL and r.critical)

        print(f"📈 Overall Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ❌ Failed: {total_failed}")
        print(f"   ⚠️  Warnings: {total_warnings}")
        print(f"   🚨 Critical Failures: {critical_failed}")

        # Results by category
        for category, results in categories.items():
            if not results:
                continue

            passed = sum(1 for r in results if r.status == TestStatus.PASS)
            failed = sum(1 for r in results if r.status == TestStatus.FAIL)
            warned = sum(1 for r in results if r.status == TestStatus.WARN)

            print(f"\n📋 {category.value.upper()} Tests:")
            print(f"   ✅ {passed}  ❌ {failed}  ⚠️  {warned}")

            # Show failed tests in this category
            failed_tests = [r for r in results if r.status == TestStatus.FAIL]
            if failed_tests:
                print(f"   Failed: {', '.join(r.name for r in failed_tests)}")

        # Performance summary
        perf_results = [r for r in self.results if r.category == TestCategory.PERFORMANCE]
        if perf_results:
            avg_time = sum(r.response_time_ms for r in perf_results) / len(perf_results)
            max_time = max(r.response_time_ms for r in perf_results)
            print(f"\n⚡ Performance Summary:")
            print(f"   Average Response Time: {avg_time:.1f}ms")
            print(f"   Slowest Response: {max_time:.1f}ms")

        # Overall verdict
        print(f"\n🎯 OVERALL VERDICT:")
        if critical_failed == 0:
            if total_failed == 0 and total_warnings == 0:
                print("   🎉 PERFECT! All tests passed.")
                print("   ✅ APIs are fully functional and ready for production.")
            elif total_warnings > 0:
                print("   ✅ GOOD! Core functionality works perfectly.")
                print("   ⚠️  Some human behavior tests failed - consider improvements.")
            else:
                print("   ✅ ACCEPTABLE! Core tests pass, non-critical issues exist.")
        else:
            print("   🚨 CRITICAL ISSUES FOUND!")
            print("   ❌ Core functionality has problems that need immediate attention.")

        return critical_failed == 0

    def save_results(self, filename: str = None):
        """Save detailed results to JSON file"""

        if filename is None:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"postal_api_test_results_{timestamp}.json"

        # Convert results to serializable format
        serializable_results = []
        for result in self.results:
            serializable_results.append({
                'name': result.name,
                'category': result.category.value,
                'status': result.status.value,
                'expected': str(result.expected),
                'actual': str(result.actual),
                'response_time_ms': result.response_time_ms,
                'details': result.details,
                'critical': result.critical
            })

        summary = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'total_tests': len(self.results),
            'passed': sum(1 for r in self.results if r.status == TestStatus.PASS),
            'failed': sum(1 for r in self.results if r.status == TestStatus.FAIL),
            'warnings': sum(1 for r in self.results if r.status == TestStatus.WARN),
            'critical_failures': sum(1 for r in self.results if r.status == TestStatus.FAIL and r.critical),
            'results': serializable_results
        }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Detailed results saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive Postal Code API Test Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 postal_api_test_suite.py                    # Test all APIs
  python3 postal_api_test_suite.py --api flask        # Test Flask only
  python3 postal_api_test_suite.py --port 5003        # Test API on port 5003
  python3 postal_api_test_suite.py --quick            # Run only core tests
  python3 postal_api_test_suite.py --human-tests      # Run only human tests
  python3 postal_api_test_suite.py --save-results     # Save JSON results
        """
    )

    parser.add_argument('--api', choices=['flask', 'fastapi'], help='Test specific API only')
    parser.add_argument('--port', type=int, help='Test API on specific port')
    parser.add_argument('--host', default='localhost', help='API host (default: localhost)')
    parser.add_argument('--quick', action='store_true', help='Run only core validation tests')
    parser.add_argument('--human-tests', action='store_true', help='Run only human behavior tests')
    parser.add_argument('--csv-tests', action='store_true', help='Run only CSV validation tests')
    parser.add_argument('--save-results', action='store_true', help='Save detailed JSON results')
    parser.add_argument('--quiet', action='store_true', help='Minimal output')

    args = parser.parse_args()

    # Initialize test suite
    suite = PostalAPITestSuite(verbose=not args.quiet)

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
        elif args.csv_tests:
            suite.run_csv_validation_tests(api_name, base_url)
        elif args.quick:
            suite.run_core_validation_tests(api_name, base_url)
        else:
            # Full test suite
            suite.run_core_validation_tests(api_name, base_url)
            suite.run_csv_validation_tests(api_name, base_url)
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