#!/usr/bin/env python3
"""
API endpoint tests for the postal code API.
Tests all endpoints with various scenarios including success, error, and edge cases.
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:5001"

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.passed = 0
        self.failed = 0

    def test(self, name: str, test_func):
        """Run a single test and report results."""
        try:
            print(f"Testing: {name}")
            result = test_func()
            if result:
                print(f"  ✅ PASS")
                self.passed += 1
            else:
                print(f"  ❌ FAIL")
                self.failed += 1
        except Exception as e:
            print(f"  ❌ ERROR: {e}")
            self.failed += 1
        print()

    def get(self, endpoint: str, params: Dict = None) -> requests.Response:
        """Make GET request to API endpoint."""
        url = f"{self.base_url}{endpoint}"
        response = requests.get(url, params=params)
        return response

    def test_health_endpoint(self) -> bool:
        """Test the health check endpoint."""
        response = self.get("/health")
        if response.status_code != 200:
            print(f"    Expected 200, got {response.status_code}")
            return False

        data = response.json()
        if data.get("status") != "healthy":
            print(f"    Expected status 'healthy', got {data.get('status')}")
            return False

        return True

    def test_postal_code_search_basic(self) -> bool:
        """Test basic postal code search."""
        response = self.get("/postal-codes", {"city": "Warszawa", "limit": 5})
        if response.status_code != 200:
            print(f"    Expected 200, got {response.status_code}")
            return False

        data = response.json()
        if "results" not in data or "count" not in data:
            print(f"    Missing required fields in response")
            return False

        if data["count"] != len(data["results"]):
            print(f"    Count mismatch: {data['count']} vs {len(data['results'])}")
            return False

        if data["count"] == 0:
            print(f"    No results found for Warszawa")
            return False

        # Check first result structure
        if data["results"]:
            result = data["results"][0]
            required_fields = ["postal_code", "city", "province"]
            for field in required_fields:
                if field not in result:
                    print(f"    Missing field '{field}' in result")
                    return False

        return True

    def test_postal_code_search_with_house_number(self) -> bool:
        """Test postal code search with house number matching."""
        # This should trigger house number matching or fallback
        response = self.get("/postal-codes", {
            "city": "Warszawa",
            "street": "Marszałkowska",
            "house_number": "100"
        })

        if response.status_code != 200:
            print(f"    Expected 200, got {response.status_code}")
            return False

        data = response.json()
        # Should either find results or provide fallback
        if data["count"] == 0:
            print(f"    No results found, not even with fallback")
            return False

        return True

    def test_postal_code_direct_lookup(self) -> bool:
        """Test direct postal code lookup."""
        # First get a postal code from search
        search_response = self.get("/postal-codes", {"city": "Warszawa", "limit": 1})
        if search_response.status_code != 200 or not search_response.json()["results"]:
            print(f"    Could not get postal code for lookup test")
            return False

        postal_code = search_response.json()["results"][0]["postal_code"]

        # Now test direct lookup
        response = self.get(f"/postal-codes/{postal_code}")
        if response.status_code != 200:
            print(f"    Expected 200, got {response.status_code}")
            return False

        data = response.json()
        if not data["results"] or data["results"][0]["postal_code"] != postal_code:
            print(f"    Postal code mismatch in direct lookup")
            return False

        return True

    def test_postal_code_not_found(self) -> bool:
        """Test postal code lookup with non-existent code."""
        response = self.get("/postal-codes/99-999")
        if response.status_code != 404:
            print(f"    Expected 404, got {response.status_code}")
            return False

        data = response.json()
        if "error" not in data:
            print(f"    Missing error message in 404 response")
            return False

        return True

    def test_locations_directory(self) -> bool:
        """Test locations directory endpoint."""
        response = self.get("/locations")
        if response.status_code != 200:
            print(f"    Expected 200, got {response.status_code}")
            return False

        data = response.json()
        if "available_endpoints" not in data:
            print(f"    Missing available_endpoints in response")
            return False

        expected_endpoints = ["provinces", "counties", "municipalities", "cities"]
        for endpoint in expected_endpoints:
            if endpoint not in data["available_endpoints"]:
                print(f"    Missing {endpoint} in available_endpoints")
                return False

        return True

    def test_provinces_endpoint(self) -> bool:
        """Test provinces endpoint."""
        response = self.get("/locations/provinces")
        if response.status_code != 200:
            print(f"    Expected 200, got {response.status_code}")
            return False

        data = response.json()
        if "provinces" not in data or "count" not in data:
            print(f"    Missing required fields in provinces response")
            return False

        if data["count"] != len(data["provinces"]):
            print(f"    Count mismatch in provinces")
            return False

        if data["count"] == 0:
            print(f"    No provinces found")
            return False

        return True

    def test_counties_endpoint(self) -> bool:
        """Test counties endpoint."""
        response = self.get("/locations/counties")
        if response.status_code != 200:
            print(f"    Expected 200, got {response.status_code}")
            return False

        data = response.json()
        if "counties" not in data or "count" not in data:
            print(f"    Missing required fields in counties response")
            return False

        return True

    def test_counties_filtered_by_province(self) -> bool:
        """Test counties endpoint filtered by province."""
        response = self.get("/locations/counties", {"province": "mazowieckie"})
        if response.status_code != 200:
            print(f"    Expected 200, got {response.status_code}")
            return False

        data = response.json()
        if data.get("filtered_by_province") != "mazowieckie":
            print(f"    Province filter not reflected in response")
            return False

        return True

    def test_search_fallback_behavior(self) -> bool:
        """Test that fallback behavior works correctly."""
        # Search for non-existent street with house number - should trigger fallbacks
        response = self.get("/postal-codes", {
            "city": "Warszawa",
            "street": "NonExistentStreetName123",
            "house_number": "999"
        })

        if response.status_code != 200:
            print(f"    Expected 200, got {response.status_code}")
            return False

        data = response.json()
        # Should have fallback_used and message
        if not data.get("fallback_used"):
            print(f"    Expected fallback to be used")
            return False

        if "message" not in data:
            print(f"    Missing fallback message")
            return False

        return True

    def test_search_limit_parameter(self) -> bool:
        """Test that limit parameter works correctly."""
        response = self.get("/postal-codes", {"city": "Warszawa", "limit": 3})
        if response.status_code != 200:
            print(f"    Expected 200, got {response.status_code}")
            return False

        data = response.json()
        if len(data["results"]) > 3:
            print(f"    Limit not respected: got {len(data['results'])} results")
            return False

        return True

    def run_all_tests(self):
        """Run all API tests."""
        print("=" * 60)
        print("POSTAL CODE API ENDPOINT TESTS")
        print("=" * 60)
        print()

        # Wait a moment for server to be ready
        time.sleep(1)

        # Health and basic functionality
        self.test("Health endpoint", self.test_health_endpoint)
        self.test("Basic postal code search", self.test_postal_code_search_basic)
        self.test("Search with house number", self.test_postal_code_search_with_house_number)
        self.test("Direct postal code lookup", self.test_postal_code_direct_lookup)
        self.test("Non-existent postal code (404)", self.test_postal_code_not_found)

        # Location hierarchy endpoints
        self.test("Locations directory", self.test_locations_directory)
        self.test("Provinces endpoint", self.test_provinces_endpoint)
        self.test("Counties endpoint", self.test_counties_endpoint)
        self.test("Counties filtered by province", self.test_counties_filtered_by_province)

        # Advanced functionality
        self.test("Search fallback behavior", self.test_search_fallback_behavior)
        self.test("Search limit parameter", self.test_search_limit_parameter)

        # Summary
        print("=" * 60)
        print(f"RESULTS: {self.passed} passed, {self.failed} failed")
        total = self.passed + self.failed
        if total > 0:
            success_rate = (self.passed / total) * 100
            print(f"Success rate: {success_rate:.1f}%")
        print("=" * 60)

        return self.failed == 0


if __name__ == "__main__":
    tester = APITester()
    success = tester.run_all_tests()
    exit(0 if success else 1)