#!/usr/bin/env python3
"""
Unit tests for postal service functions.
Tests the service layer logic without requiring the API to be running.
"""

import unittest
import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from postal_service import build_search_query, filter_by_house_number
from house_number_matcher import is_house_number_in_range

class MockRow:
    """Mock database row for testing."""
    def __init__(self, **kwargs):
        self._data = kwargs

    def __getitem__(self, key):
        return self._data.get(key)

class TestPostalService(unittest.TestCase):
    """Test postal service functions."""

    def test_build_search_query_basic(self):
        """Test basic query building."""
        query, params = build_search_query(city="Warszawa")

        self.assertIn("SELECT * FROM postal_codes", query)
        self.assertIn("city LIKE ? COLLATE NOCASE", query)
        self.assertEqual(params[0], "Warszawa%")

    def test_build_search_query_all_params(self):
        """Test query building with all parameters."""
        query, params = build_search_query(
            city="Warszawa",
            street="Marszałkowska",
            province="mazowieckie",
            county="Warszawa",
            municipality="Warszawa",
            limit=50
        )

        self.assertIn("city LIKE ? COLLATE NOCASE", query)
        self.assertIn("street LIKE ? COLLATE NOCASE", query)
        self.assertIn("province = ? COLLATE NOCASE", query)
        self.assertIn("county = ? COLLATE NOCASE", query)
        self.assertIn("municipality = ? COLLATE NOCASE", query)

        expected_params = ["Warszawa%", "%Marszałkowska%", "mazowieckie", "Warszawa", "Warszawa", 50]
        self.assertEqual(params, expected_params)

    def test_build_search_query_with_house_number(self):
        """Test query building with house number (should use larger limit)."""
        query, params = build_search_query(
            city="Warszawa",
            house_number="123",
            limit=10
        )

        # Should use min(limit * 5, 1000) = min(50, 1000) = 50
        self.assertEqual(params[-1], 50)

    def test_filter_by_house_number_no_house_number(self):
        """Test filtering when no house number is provided."""
        mock_rows = [
            MockRow(house_numbers="1-10", postal_code="00-001"),
            MockRow(house_numbers="11-20", postal_code="00-002"),
            MockRow(house_numbers="21-30", postal_code="00-003"),
        ]

        result = filter_by_house_number(mock_rows, None, 2)
        self.assertEqual(len(result), 2)

    def test_filter_by_house_number_with_matching(self):
        """Test filtering with house number matching."""
        mock_rows = [
            MockRow(house_numbers="1-10", postal_code="00-001"),
            MockRow(house_numbers="11-20", postal_code="00-002"),
            MockRow(house_numbers="21-30", postal_code="00-003"),
        ]

        result = filter_by_house_number(mock_rows, "5", 10)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["postal_code"], "00-001")

    def test_filter_by_house_number_with_side_indicators(self):
        """Test filtering with side indicators."""
        mock_rows = [
            MockRow(house_numbers="1-19(n)", postal_code="00-001"),  # odd
            MockRow(house_numbers="2-20(p)", postal_code="00-002"),  # even
        ]

        # Test odd number
        result = filter_by_house_number(mock_rows, "5", 10)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["postal_code"], "00-001")

        # Test even number
        result = filter_by_house_number(mock_rows, "6", 10)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["postal_code"], "00-002")

    def test_filter_by_house_number_no_house_numbers_field(self):
        """Test filtering when records don't have house_numbers field."""
        mock_rows = [
            MockRow(house_numbers=None, postal_code="00-001"),
            MockRow(house_numbers="", postal_code="00-002"),
            MockRow(house_numbers="1-10", postal_code="00-003"),
        ]

        result = filter_by_house_number(mock_rows, "5", 10)
        # Only the third row should match
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["postal_code"], "00-003")

    def test_filter_by_house_number_limit_respected(self):
        """Test that the limit is respected during filtering."""
        mock_rows = [
            MockRow(house_numbers="1-100", postal_code=f"00-00{i}")
            for i in range(10)
        ]

        result = filter_by_house_number(mock_rows, "50", 3)
        self.assertEqual(len(result), 3)

class TestHouseNumberMatcherIntegration(unittest.TestCase):
    """Integration tests for house number matcher with various Polish patterns."""

    def test_complex_real_world_patterns(self):
        """Test real-world complex patterns from Polish postal database."""
        test_cases = [
            # Complex slash notation
            ("1", "1/3-23/25(n)", True),    # 1 is in first part and odd
            ("3", "1/3-23/25(n)", True),    # 3 is in first part and odd
            ("23", "1/3-23/25(n)", True),   # 23 is in second part and odd
            ("25", "1/3-23/25(n)", True),   # 25 is in second part and odd
            ("2", "1/3-23/25(n)", False),   # 2 is even
            ("24", "1/3-23/25(n)", False),  # 24 is even

            # DK ranges with letters
            ("6a", "6a-DK", True),
            ("6", "6a-DK", False),  # Plain 6 should not match 6a-DK
            ("7", "6a-DK", True),   # But higher numbers should match
            ("100", "6a-DK", True),

            # Letter ranges
            ("31", "31-31a", True),
            ("31a", "31-31a", True),
            ("32", "31-31a", False),

            # Individual numbers with letters
            ("35c", "35c", True),
            ("35", "35c", False),
            ("35a", "35c", False),
        ]

        for house_num, pattern, expected in test_cases:
            with self.subTest(house_number=house_num, pattern=pattern):
                result = is_house_number_in_range(house_num, pattern)
                self.assertEqual(result, expected,
                    f"Pattern '{pattern}' with house number '{house_num}' should be {expected}")

    def test_performance_patterns(self):
        """Test patterns that might cause performance issues."""
        # Test with very large ranges
        large_range_patterns = [
            ("1", "1-10000", True),
            ("5000", "1-10000", True),
            ("10000", "1-10000", True),
            ("10001", "1-10000", False),
        ]

        for house_num, pattern, expected in large_range_patterns:
            with self.subTest(house_number=house_num, pattern=pattern):
                result = is_house_number_in_range(house_num, pattern)
                self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()