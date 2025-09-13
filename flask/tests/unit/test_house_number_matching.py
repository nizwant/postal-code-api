#!/usr/bin/env python3
"""
Comprehensive test suite for Polish postal code house number matching.

Tests individual normalized patterns that appear in the database after
comma-separated ranges have been split into separate records.
"""

import unittest
from house_number_matcher import is_house_number_in_range

class TestHouseNumberMatching(unittest.TestCase):
    """Test individual normalized house number patterns."""

    def test_simple_ranges(self):
        """Test simple numeric ranges."""
        test_cases = [
            ("2", "1-12", True),
            ("12", "1-12", True),
            ("1", "1-12", True),
            ("13", "1-12", False),
            ("0", "1-12", False),
        ]
        self._run_test_cases(test_cases)

    def test_side_indicators(self):
        """Test ranges with (n) = odd and (p) = even indicators."""
        test_cases = [
            # Odd numbers (n)
            ("1", "1-41(n)", True),
            ("2", "1-41(n)", False),
            ("41", "1-41(n)", True),
            ("42", "1-41(n)", False),
            ("21", "1-41(n)", True),
            ("22", "1-41(n)", False),

            # Even numbers (p)
            ("2", "2-38(p)", True),
            ("3", "2-38(p)", False),
            ("38", "2-38(p)", True),
            ("39", "2-38(p)", False),
            ("20", "2-38(p)", True),
            ("21", "2-38(p)", False),
        ]
        self._run_test_cases(test_cases)

    def test_dk_ranges(self):
        """Test DK (do końca / to the end) ranges."""
        test_cases = [
            # Simple DK
            ("337", "337-DK", True),
            ("500", "337-DK", True),
            ("9999", "337-DK", True),
            ("336", "337-DK", False),

            # DK with side indicators
            ("2", "2-DK(p)", True),
            ("100", "2-DK(p)", True),
            ("1001", "2-DK(p)", False),
            ("1", "2-DK(p)", False),
            ("5", "5-DK(n)", True),
            ("101", "5-DK(n)", True),
            ("4", "5-DK(n)", False),
            ("100", "5-DK(n)", False),
        ]
        self._run_test_cases(test_cases)

    def test_individual_numbers(self):
        """Test exact individual numbers."""
        test_cases = [
            ("60", "60", True),
            ("61", "60", False),
            ("35c", "35c", True),
            ("35", "35c", False),  # Should be exact for letters
            ("125", "125", True),
            ("124", "125", False),
        ]
        self._run_test_cases(test_cases)

    def test_letter_suffixes(self):
        """Test ranges with letter suffixes."""
        test_cases = [
            # Simple letter ranges
            ("31", "31-31a", True),
            ("31a", "31-31a", True),
            ("32", "31-31a", False),

            # Letter ranges
            ("22", "22-22b", True),
            ("22a", "22-22b", True),
            ("22b", "22-22b", True),
            ("23", "22-22b", False),
        ]
        self._run_test_cases(test_cases)

    def test_slash_notation(self):
        """Test slash notation patterns."""
        test_cases = [
            # Simple slash list: "2/4"
            ("2", "2/4", True),
            ("4", "2/4", True),
            ("3", "2/4", False),

            # Slash range: "55-69/71(n)"
            ("55", "55-69/71(n)", True),
            ("69", "55-69/71(n)", True),
            ("71", "55-69/71(n)", True),
            ("56", "55-69/71(n)", False),  # even in odd range
            ("70", "55-69/71(n)", False),  # even in odd range
            ("72", "55-69/71(n)", False),  # out of range

            # Slash start range: "2/4-10(p)"
            ("2", "2/4-10(p)", False),  # 2 is not in the range (per original test spec)
            ("4", "2/4-10(p)", True),
            ("6", "2/4-10(p)", True),
            ("10", "2/4-10(p)", True),
            ("5", "2/4-10(p)", False),  # odd in even range
        ]
        self._run_test_cases(test_cases)

    def test_real_database_patterns(self):
        """Test patterns actually found in the normalized database."""
        test_cases = [
            # From validation examples
            ("17", "17-21(n)", True),
            ("18", "17-21(n)", False),
            ("19", "17-21(n)", True),
            ("21", "17-21(n)", True),
            ("22", "17-21(n)", False),

            ("2", "2-60(p)", True),
            ("60", "2-60(p)", True),
            ("3", "2-60(p)", False),
            ("61", "2-60(p)", False),

            ("30", "30-DK(p)", True),
            ("100", "30-DK(p)", True),
            ("31", "30-DK(p)", False),
            ("29", "30-DK(p)", False),
        ]
        self._run_test_cases(test_cases)

    def test_complex_slash_patterns(self):
        """Test complex slash patterns found in the database."""
        test_cases = [
            # Complex slash pattern: "1/3-23/25(n)"
            ("1", "1/3-23/25(n)", True),   # Individual number, odd
            ("3", "1/3-23/25(n)", True),   # Individual number, odd
            ("23", "1/3-23/25(n)", True),  # Individual number, odd
            ("25", "1/3-23/25(n)", True),  # Individual number, odd
            ("2", "1/3-23/25(n)", False),  # Even number
            ("24", "1/3-23/25(n)", False), # Even number
            ("5", "1/3-23/25(n)", False),  # Not in the specific list
        ]
        self._run_test_cases(test_cases)

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        test_cases = [
            # Empty inputs
            ("", "1-10", False),
            ("1", "", False),
            ("", "", False),

            # Invalid inputs
            ("abc", "1-10", False),
            ("1", "invalid", False),

            # Boundary conditions
            ("1", "1-1", True),
            ("2", "1-1", False),

            # Letter edge cases with DK ranges
            ("6", "6a-DK(p)", False),  # 6 != 6a
            ("8", "6a-DK(p)", True),   # 8 is even and >= 6
        ]
        self._run_test_cases(test_cases)

    def _run_test_cases(self, test_cases):
        """Helper to run a list of test cases."""
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                result = is_house_number_in_range(house_num, range_str)
                self.assertEqual(result, expected,
                    f"House number '{house_num}' in range '{range_str}' should be {expected}, got {result}")

    def test_production_patterns(self):
        """Test against actual patterns from the production database."""
        # These are real patterns from the normalized database
        test_cases = [
            # Warsaw street examples (normalized)
            ("5", "1-19(n)", True),     # Odd number in odd range
            ("6", "2-16a(p)", True),    # Even number in even range
            ("25", "21-DK(n)", True),   # Odd number in DK odd range
            ("20", "18-DK(p)", True),   # Even number in DK even range

            # Individual numbers
            ("616", "616", True),
            ("617", "616", False),

            # DK ranges
            ("1000", "1-DK", True),
            ("0", "1-DK", False),
        ]
        self._run_test_cases(test_cases)

if __name__ == '__main__':
    # Run the tests with verbose output
    unittest.main(verbosity=2)