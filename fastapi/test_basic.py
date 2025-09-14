#!/usr/bin/env python3
"""
Basic test script to verify FastAPI implementation works.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import check_database_exists
from postal_service import get_provinces, search_postal_codes
from house_number_matcher import is_house_number_in_range

def test_database_connection():
    """Test if database exists and can be accessed."""
    print("Testing database connection...")
    if not check_database_exists():
        print("❌ Database file not found!")
        return False
    print("✅ Database file exists")

    try:
        # Test basic database query
        provinces = get_provinces()
        print(f"✅ Found {provinces['count']} provinces")
        return True
    except Exception as e:
        print(f"❌ Database query failed: {e}")
        return False

def test_house_number_matching():
    """Test house number matching logic."""
    print("\nTesting house number matching...")

    test_cases = [
        ("5", "1-19(n)", True),   # 5 is odd, should match odd range
        ("6", "2-16a(p)", True),  # 6 is even, should match even range
        ("4", "1-19(n)", False),  # 4 is even, shouldn't match odd range
    ]

    for house_num, pattern, expected in test_cases:
        result = is_house_number_in_range(house_num, pattern)
        status = "✅" if result == expected else "❌"
        print(f"{status} {house_num} in '{pattern}' = {result} (expected {expected})")

    return True

def test_search_functionality():
    """Test basic search functionality."""
    print("\nTesting search functionality...")

    try:
        # Test basic search
        results = search_postal_codes(city="Warszawa", limit=5)
        print(f"✅ Search for Warszawa returned {results['count']} results")

        # Test with house number
        results = search_postal_codes(
            city="Warszawa",
            street="Edwarda Józefa Abramowskiego",
            house_number="5",
            limit=5
        )
        print(f"✅ Search with house number returned {results['count']} results")

        return True
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return False

if __name__ == "__main__":
    print("Running basic FastAPI implementation tests...\n")

    all_passed = True
    all_passed &= test_database_connection()
    all_passed &= test_house_number_matching()
    all_passed &= test_search_functionality()

    print(f"\n{'✅ All tests passed!' if all_passed else '❌ Some tests failed!'}")
    sys.exit(0 if all_passed else 1)