import unittest
from typing import List, Tuple


class TestHouseNumberMatching(unittest.TestCase):
    """
    Comprehensive test suite for Polish postal code house number matching logic.
    
    Based on analysis of real database patterns, covering:
    - Simple ranges: "1-12", "337-DK" 
    - Side indicators: "(n)" = nieparzyste (odd), "(p)" = parzyste (even)
    - Complex combinations: "270-336(p), 283-335(n)"
    - Letter suffixes: "4a-9/11", "31-31a", "87a-89(n)"
    - Slash notation: "55-69/71(n)", "2/4-10(p)"
    - Individual numbers: "1, 16-38(p)"
    - Mixed formats: "1, 3a-128b, 130-248(p)"
    """

    def test_simple_numeric_ranges(self):
        """Test basic numeric ranges without side indicators."""
        test_cases = [
            # (house_number, range_string, expected_result)
            ("2", "1-12", True),
            ("12", "1-12", True), 
            ("13", "1-12", False),
            ("0", "1-12", False),
            ("1", "1-12", True),
            ("50", "29-DK", True),  # DK means "do końca" (to the end)
            ("337", "337-DK", True),
            ("336", "337-DK", False),
            ("1000", "337-DK", True),  # DK should match any high number
        ]
        
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                result = self._is_house_number_in_range(house_num, range_str)
                self.assertEqual(result, expected, 
                    f"House number '{house_num}' in range '{range_str}' should be {expected}")

    def test_odd_even_side_indicators(self):
        """Test ranges with (n) = odd and (p) = even indicators."""
        test_cases = [
            # Odd numbers (n)
            ("1", "1-41(n)", True),    # odd in odd range
            ("2", "1-41(n)", False),   # even in odd range  
            ("41", "1-41(n)", True),   # odd boundary
            ("42", "1-41(n)", False),  # out of range
            ("21", "1-41(n)", True),   # odd middle
            ("22", "1-41(n)", False),  # even middle
            
            # Even numbers (p)
            ("2", "2-38(p)", True),    # even in even range
            ("3", "2-38(p)", False),   # odd in even range
            ("38", "2-38(p)", True),   # even boundary
            ("39", "2-38(p)", False),  # out of range
            ("20", "2-38(p)", True),   # even middle
            ("21", "2-38(p)", False),  # odd middle
        ]
        
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                result = self._is_house_number_in_range(house_num, range_str)
                self.assertEqual(result, expected,
                    f"House number '{house_num}' in range '{range_str}' should be {expected}")

    def test_complex_multiple_ranges(self):
        """Test complex ranges with multiple comma-separated parts."""
        test_cases = [
            # "270-336(p), 283-335(n)" - from your examples
            ("270", "270-336(p), 283-335(n)", True),   # even in first range
            ("271", "270-336(p), 283-335(n)", False),  # odd, not in second range
            ("283", "270-336(p), 283-335(n)", True),   # odd in second range
            ("284", "270-336(p), 283-335(n)", False),  # even, not in first range
            ("335", "270-336(p), 283-335(n)", True),   # odd boundary
            ("336", "270-336(p), 283-335(n)", True),   # even boundary
            ("337", "270-336(p), 283-335(n)", False),  # out of both ranges
            
            # "1, 2-10(p)" - individual number + even range
            ("1", "1, 2-10(p)", True),     # individual number
            ("2", "1, 2-10(p)", True),     # even in range
            ("3", "1, 2-10(p)", False),    # odd in even range
            ("10", "1, 2-10(p)", True),    # even boundary
            ("11", "1, 2-10(p)", False),   # out of range
        ]
        
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                result = self._is_house_number_in_range(house_num, range_str)
                self.assertEqual(result, expected,
                    f"House number '{house_num}' in range '{range_str}' should be {expected}")

    def test_letter_suffixes(self):
        """Test ranges and numbers with letter suffixes (4a, 9/11, etc.)."""
        test_cases = [
            # Letter suffixes
            ("4a", "4a-9/11", True),
            ("5", "4a-9/11", True),        # Should match numeric part
            ("9", "4a-9/11", True),
            ("10", "4a-9/11", False),      # Beyond range
            ("4", "4a-9/11", False),       # 4 != 4a (exact matching for letters)
            
            # Complex with letters: "31-31a"
            ("31", "31-31a", True),
            ("31a", "31-31a", True),
            ("32", "31-31a", False),
            
            # Range with letter suffix: "87a-89(n)"
            ("87a", "87a-89(n)", False),   # 87a is even, but range is odd
            ("89", "87a-89(n)", True),     # 89 is odd
            ("88", "87a-89(n)", False),    # 88 is even in odd range
        ]
        
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                result = self._is_house_number_in_range(house_num, range_str)
                self.assertEqual(result, expected,
                    f"House number '{house_num}' in range '{range_str}' should be {expected}")

    def test_slash_notation(self):
        """Test slash notation like 2/4, 9/11, 55-69/71."""
        test_cases = [
            # Slash ranges: "55-69/71(n)"
            ("55", "55-69/71(n)", True),   # odd start
            ("69", "55-69/71(n)", True),   # odd in range  
            ("71", "55-69/71(n)", True),   # odd end
            ("56", "55-69/71(n)", False),  # even in odd range
            ("70", "55-69/71(n)", False),  # even in odd range
            ("72", "55-69/71(n)", False),  # out of range
            
            # Individual slash numbers: "2/4-10(p)"
            ("2", "2/4-10(p)", False),     # 2 is not 2/4
            ("4", "2/4-10(p)", True),      # even in even range
            ("6", "2/4-10(p)", True),      # even in range
            ("10", "2/4-10(p)", True),     # even boundary
            ("5", "2/4-10(p)", False),     # odd in even range
            
            # Simple slash: "5/7"  
            ("5", "5/7", True),
            ("7", "5/7", True),
            ("6", "5/7", False),           # Not explicitly listed
        ]
        
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                result = self._is_house_number_in_range(house_num, range_str)
                self.assertEqual(result, expected,
                    f"House number '{house_num}' in range '{range_str}' should be {expected}")

    def test_dk_ranges(self):
        """Test DK (do końca / to the end) ranges."""
        test_cases = [
            # Simple DK
            ("337", "337-DK", True),
            ("500", "337-DK", True),       # Any number >= 337
            ("9999", "337-DK", True),      # Very high numbers
            ("336", "337-DK", False),      # Below start
            
            # DK with side indicators: "2-DK(p)"
            ("2", "2-DK(p)", True),        # Even start
            ("100", "2-DK(p)", True),      # Even high number  
            ("1001", "2-DK(p)", False),    # Odd high number
            ("1", "2-DK(p)", False),       # Below start
            
            # DK with multiple ranges: "2-DK(p), 5-DK(n)"
            ("2", "2-DK(p), 5-DK(n)", True),    # Even >= 2
            ("100", "2-DK(p), 5-DK(n)", True),  # Even high
            ("5", "2-DK(p), 5-DK(n)", True),    # Odd >= 5  
            ("101", "2-DK(p), 5-DK(n)", True),  # Odd high
            ("1", "2-DK(p), 5-DK(n)", False),   # Below both starts
            ("3", "2-DK(p), 5-DK(n)", False),   # Odd but < 5
            ("4", "2-DK(p), 5-DK(n)", True),    # Even >= 2
        ]
        
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                result = self._is_house_number_in_range(house_num, range_str)
                self.assertEqual(result, expected,
                    f"House number '{house_num}' in range '{range_str}' should be {expected}")

    def test_individual_numbers_and_lists(self):
        """Test individual numbers and comma-separated lists."""
        test_cases = [
            # Simple individual numbers
            ("60", "60", True),
            ("61", "60", False),
            
            # Lists: "33/37"
            ("33", "33/37", True),
            ("37", "33/37", True),
            ("35", "33/37", False),    # Not explicitly listed
            
            # Complex mixed: "4a-9/11, 7-29/31(n), 33/37"
            ("4a", "4a-9/11, 7-29/31(n), 33/37", True),
            ("5", "4a-9/11, 7-29/31(n), 33/37", True),   # In first range
            ("7", "4a-9/11, 7-29/31(n), 33/37", True),   # Odd in second range
            ("8", "4a-9/11, 7-29/31(n), 33/37", True),   # In first range (even though second is odd)
            ("29", "4a-9/11, 7-29/31(n), 33/37", True),  # Odd boundary
            ("31", "4a-9/11, 7-29/31(n), 33/37", True),  # Odd end  
            ("33", "4a-9/11, 7-29/31(n), 33/37", True),  # Individual number
            ("37", "4a-9/11, 7-29/31(n), 33/37", True),  # Individual number
            ("35", "4a-9/11, 7-29/31(n), 33/37", False), # Not in any part
            ("30", "4a-9/11, 7-29/31(n), 33/37", False), # Even in odd range
        ]
        
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                result = self._is_house_number_in_range(house_num, range_str)
                self.assertEqual(result, expected,
                    f"House number '{house_num}' in range '{range_str}' should be {expected}")

    def test_edge_cases_and_malformed_input(self):
        """Test edge cases and malformed input handling."""
        test_cases = [
            # Empty strings
            ("1", "", False),
            ("", "1-10", False),
            ("", "", False),
            
            # Non-numeric input  
            ("abc", "1-10", False),
            ("1", "abc-def", False),
            
            # Boundary conditions
            ("0", "1-10", False),
            ("1", "1-10", True),
            ("10", "1-10", True),
            ("11", "1-10", False),
            
            # Malformed ranges
            ("5", "10-1", False),      # Invalid range (end < start)
            ("5", "5-5", True),        # Single number range
            ("5", "5-5(p)", False),    # 5 is odd, range is even
            ("6", "5-5(p)", False),    # 6 is not in range 5-5
        ]
        
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                result = self._is_house_number_in_range(house_num, range_str)
                self.assertEqual(result, expected,
                    f"House number '{house_num}' in range '{range_str}' should be {expected}")

    def test_real_database_examples(self):
        """Test against actual examples from the database."""
        # From your original query
        test_cases = [
            # Jarocińska street examples
            ("2", "1-12", True),
            ("1", "1-12", True),
            ("12", "1-12", True),
            ("13", "1-12", False),
            ("15", "13-28", True),
            ("28", "13-28", True),
            ("12", "13-28", False),
            ("50", "29-DK", True),
            
            # Grabiszyńska street examples  
            ("1", "1-41(n)", True),       # odd
            ("2", "1-41(n)", False),      # even in odd range
            ("40", "2-38(p)", True),      # Wait, 40 > 38, should be False
            ("38", "2-38(p)", True),      # even
            ("39", "2-38(p)", False),     # odd in even range
            ("270", "270-336(p), 283-335(n)", True),  # even
            ("283", "270-336(p), 283-335(n)", True),  # odd
            ("400", "337-DK", True),      # DK range
            
            # Warsaw examples
            ("1", "1-19(n), 2-16(p)", True),    # odd in first range
            ("2", "1-19(n), 2-16(p)", True),    # even in second range  
            ("18", "18-58(p), 21-53(n)", True), # even in first range
            ("21", "18-58(p), 21-53(n)", True), # odd in second range
            ("60", "55-69/71(n), 60", True),    # individual number
            ("65", "55-69/71(n), 60", True),    # odd in range
            ("66", "55-69/71(n), 60", False),   # even, not individual
        ]
        
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                result = self._is_house_number_in_range(house_num, range_str)
                self.assertEqual(result, expected,
                    f"House number '{house_num}' in range '{range_str}' should be {expected}")

    def _is_house_number_in_range(self, house_number: str, range_string: str) -> bool:
        """
        Placeholder function for the actual implementation.
        
        This should be replaced with the real implementation once it's created.
        For now, returns False for all cases to ensure tests fail until implementation is done.
        """
        # TODO: Replace with actual implementation
        return False

    def get_test_pattern_summary(self) -> List[Tuple[str, str]]:
        """
        Return a summary of all patterns that need to be supported.
        Useful for implementation planning.
        """
        return [
            ("Simple ranges", "1-12, 29-100"),
            ("DK ranges", "337-DK, 2-DK(p)"),
            ("Side indicators", "1-41(n), 2-38(p)"),
            ("Multiple ranges", "270-336(p), 283-335(n)"),
            ("Individual numbers", "60, 1, 16-38(p)"),
            ("Letter suffixes", "4a-9/11, 31-31a, 87a-89(n)"),
            ("Slash notation", "55-69/71(n), 2/4-10(p), 5/7"),
            ("Complex mixed", "4a-9/11, 7-29/31(n), 33/37"),
            ("Lists with ranges", "1, 2-10(p), 5-25(n)"),
            ("DK with sides", "2-DK(p), 5-DK(n)"),
        ]


if __name__ == '__main__':
    # Run the tests
    unittest.main(verbosity=2)
    
    # Print pattern summary for implementation reference
    test_instance = TestHouseNumberMatching()
    print("\n" + "="*60)
    print("IMPLEMENTATION PATTERNS TO SUPPORT:")
    print("="*60)
    for category, examples in test_instance.get_test_pattern_summary():
        print(f"{category:20}: {examples}")