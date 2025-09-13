#!/usr/bin/env python3
"""
Main test runner for the Postal Code API.

This script runs all tests including:
- Unit tests for house number matching
- Unit tests for postal service functions
- API integration tests

Usage:
    python run_tests.py                    # Run all tests
    python run_tests.py --unit-only        # Run only unit tests
    python run_tests.py --api-only         # Run only API tests
    python run_tests.py --check-server     # Check if server is running
"""

import argparse
import subprocess
import sys
import os
import time
import requests
from urllib3.exceptions import InsecureRequestWarning

# Suppress SSL warnings for localhost testing
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


class TestRunner:
    def __init__(self):
        self.server_url = "http://localhost:5001"
        self.results = {
            "unit_tests": {"passed": 0, "failed": 0, "total": 0},
            "api_tests": {"passed": 0, "failed": 0, "total": 0},
            "overall": {"passed": 0, "failed": 0, "total": 0},
        }

    def check_server_running(self) -> bool:
        """Check if the Flask server is running."""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def run_unit_tests(self) -> bool:
        """Run all unit tests using unittest."""
        print("=" * 60)
        print("RUNNING UNIT TESTS")
        print("=" * 60)

        # Run house number matching tests
        print("\n📋 Running house number matching tests...")
        result1 = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                "tests.unit.test_house_number_matching",
                "-v",
            ],
            capture_output=True,
            text=True,
        )

        print(result1.stdout)
        if result1.stderr:
            print("STDERR:", result1.stderr)

        # Run postal service tests
        print("\n📋 Running postal service tests...")
        result2 = subprocess.run(
            [sys.executable, "-m", "unittest", "tests.unit.test_postal_service", "-v"],
            capture_output=True,
            text=True,
        )

        print(result2.stdout)
        if result2.stderr:
            print("STDERR:", result2.stderr)

        # Parse results (basic parsing)
        unit_success = result1.returncode == 0 and result2.returncode == 0

        # Count tests from output
        output = result1.stdout + result2.stdout
        if "Ran" in output:
            for line in output.split("\n"):
                if line.startswith("Ran "):
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            test_count = int(parts[1])
                            self.results["unit_tests"]["total"] += test_count
                            if unit_success:
                                self.results["unit_tests"]["passed"] += test_count
                            else:
                                self.results["unit_tests"]["failed"] += test_count
                        except ValueError:
                            pass

        print(f"\n📊 Unit tests result: {'✅ PASSED' if unit_success else '❌ FAILED'}")
        return unit_success

    def run_api_tests(self) -> bool:
        """Run API integration tests."""
        print("=" * 60)
        print("RUNNING API INTEGRATION TESTS")
        print("=" * 60)

        # Check if server is running
        if not self.check_server_running():
            print("❌ Flask server is not running!")
            print(f"Please start the server with: python app.py")
            print(f"Server should be available at: {self.server_url}")
            return False

        print(f"✅ Server is running at {self.server_url}")

        # Run API tests
        result = subprocess.run(
            [sys.executable, "tests/api/test_endpoints.py"],
            capture_output=True,
            text=True,
        )

        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        # Parse API test results
        api_success = result.returncode == 0

        # Try to parse the results from the custom API test output
        output_lines = result.stdout.split("\n")
        for line in output_lines:
            if "RESULTS:" in line:
                # Parse "RESULTS: X passed, Y failed"
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.isdigit():
                        if i > 0 and parts[i - 1] in ["RESULTS:", "passed,"]:
                            if "passed" in parts[i + 1] if i + 1 < len(parts) else "":
                                self.results["api_tests"]["passed"] = int(part)
                        elif (
                            i > 0 and "failed" in parts[i + 1]
                            if i + 1 < len(parts)
                            else ""
                        ):
                            self.results["api_tests"]["failed"] = int(part)

        self.results["api_tests"]["total"] = (
            self.results["api_tests"]["passed"] + self.results["api_tests"]["failed"]
        )

        print(f"\n📊 API tests result: {'✅ PASSED' if api_success else '❌ FAILED'}")
        return api_success

    def print_summary(self, unit_success: bool, api_success: bool):
        """Print overall test summary."""
        # Calculate totals
        self.results["overall"]["passed"] = (
            self.results["unit_tests"]["passed"] + self.results["api_tests"]["passed"]
        )
        self.results["overall"]["failed"] = (
            self.results["unit_tests"]["failed"] + self.results["api_tests"]["failed"]
        )
        self.results["overall"]["total"] = (
            self.results["overall"]["passed"] + self.results["overall"]["failed"]
        )

        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        # Unit tests summary
        print(f"📋 Unit Tests:")
        print(f"   Passed: {self.results['unit_tests']['passed']}")
        print(f"   Failed: {self.results['unit_tests']['failed']}")
        print(f"   Total:  {self.results['unit_tests']['total']}")
        print(f"   Status: {'✅ PASSED' if unit_success else '❌ FAILED'}")

        # API tests summary
        print(f"\n🌐 API Tests:")
        print(f"   Passed: {self.results['api_tests']['passed']}")
        print(f"   Failed: {self.results['api_tests']['failed']}")
        print(f"   Total:  {self.results['api_tests']['total']}")
        print(f"   Status: {'✅ PASSED' if api_success else '❌ FAILED'}")

        # Overall summary
        overall_success = unit_success and api_success
        total_tests = self.results["overall"]["total"]

        print(f"\n🎯 Overall Results:")
        print(f"   Total Passed: {self.results['overall']['passed']}")
        print(f"   Total Failed: {self.results['overall']['failed']}")
        print(f"   Total Tests:  {total_tests}")

        if total_tests > 0:
            success_rate = (self.results["overall"]["passed"] / total_tests) * 100
            print(f"   Success Rate: {success_rate:.1f}%")

        print(
            f"   Overall Status: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}"
        )
        print("=" * 60)

        return overall_success

    def run_all_tests(self, unit_only=False, api_only=False):
        """Run all tests or specific subset."""
        print("🧪 Postal Code API Test Suite")
        print(f"📍 Current directory: {os.getcwd()}")
        print(f"🐍 Python version: {sys.version.split()[0]}")
        print()

        unit_success = True
        api_success = True

        if not api_only:
            unit_success = self.run_unit_tests()

        if not unit_only:
            api_success = self.run_api_tests()

        overall_success = self.print_summary(unit_success, api_success)
        return overall_success


def main():
    parser = argparse.ArgumentParser(description="Run Postal Code API tests")
    parser.add_argument("--unit-only", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--api-only", action="store_true", help="Run only API integration tests"
    )
    parser.add_argument(
        "--check-server",
        action="store_true",
        help="Check if server is running and exit",
    )

    args = parser.parse_args()

    runner = TestRunner()

    if args.check_server:
        if runner.check_server_running():
            print(f"✅ Server is running at {runner.server_url}")
            sys.exit(0)
        else:
            print(f"❌ Server is not running at {runner.server_url}")
            sys.exit(1)

    success = runner.run_all_tests(unit_only=args.unit_only, api_only=args.api_only)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
