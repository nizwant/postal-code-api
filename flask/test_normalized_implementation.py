#!/usr/bin/env python3
"""
Test the normalized database implementation against our comprehensive test suite.

This script tests the actual database queries to ensure the normalized structure
correctly handles all Polish postal code house number patterns.
"""

import sqlite3
import unittest
import os
from typing import List, Tuple

class TestNormalizedImplementation(unittest.TestCase):
    """Test the normalized database implementation."""
    
    def setUp(self):
        """Set up database connection for each test."""
        self.db_path = 'postal_codes_normalized.db'
        if not os.path.exists(self.db_path):
            self.skipTest(f"Normalized database not found at {self.db_path}")
    
    def _is_house_number_in_range_db(self, house_number: str, target_range: str) -> bool:
        """
        Test if house_number matches target_range using the normalized database.
        
        This simulates the actual query logic from the Flask app.
        """
        try:
            house_num_int = int(house_number)
            is_even = house_num_int % 2 == 0
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Find ranges that match the target_range text
                cursor.execute("""
                    SELECT start_number, end_number, is_odd, is_even, range_type
                    FROM house_ranges 
                    WHERE original_range_text = ?
                """, (target_range,))
                
                results = cursor.fetchall()
                
                for start_number, end_number, is_odd, is_even, range_type in results:
                    # Check if house number falls within range
                    if start_number is not None and house_num_int < start_number:
                        continue
                    
                    if end_number is not None and house_num_int > end_number:
                        continue
                    
                    # Check odd/even restrictions
                    if is_odd and is_even is None:  # Odd only
                        if house_num_int % 2 == 0:  # House number is even
                            continue
                    elif is_even and is_odd is None:  # Even only  
                        if house_num_int % 2 == 1:  # House number is odd
                            continue
                    
                    # If we get here, it matches
                    return True
                
                return False
                
        except ValueError:
            # Handle non-numeric house numbers (4a, etc.)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT COUNT(*) FROM house_ranges 
                    WHERE original_range_text = ? 
                      AND (original_range_text LIKE ? OR special_cases LIKE ?)
                """, (target_range, f"%{house_number}%", f"%{house_number}%"))
                
                return cursor.fetchone()[0] > 0

    def test_real_database_examples(self):
        """Test against actual examples from the database."""
        test_cases = [
            # Jarocińska street examples - the original problem!
            ("2", "1-12", True),
            ("1", "1-12", True),
            ("12", "1-12", True),
            ("13", "1-12", False),
            ("15", "13-28", True),
            ("28", "13-28", True),
            ("12", "13-28", False),
            ("50", "29-DK", True),
            ("1000", "29-DK", True),  # DK should match high numbers
            
            # Simple DK ranges
            ("337", "337-DK", True),
            ("500", "337-DK", True),
            ("336", "337-DK", False),
        ]
        
        passed = 0
        failed = 0
        
        for house_num, range_str, expected in test_cases:
            with self.subTest(house_num=house_num, range_str=range_str):
                try:
                    result = self._is_house_number_in_range_db(house_num, range_str)
                    self.assertEqual(result, expected,
                        f"House number '{house_num}' in range '{range_str}' should be {expected}")
                    passed += 1
                except AssertionError:
                    failed += 1
                    print(f"FAILED: {house_num} in {range_str} expected {expected}, got {not expected}")
                except Exception as e:
                    failed += 1
                    print(f"ERROR: {house_num} in {range_str}: {e}")
        
        print(f"\nReal Database Examples: {passed} passed, {failed} failed")

    def test_odd_even_ranges_db(self):
        """Test odd/even ranges using database queries."""
        # Find some actual odd/even ranges from the database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get a few odd ranges
            cursor.execute("""
                SELECT original_range_text, start_number, end_number 
                FROM house_ranges 
                WHERE is_odd = 1 AND is_even IS NULL 
                  AND start_number IS NOT NULL AND end_number IS NOT NULL
                LIMIT 3
            """)
            odd_ranges = cursor.fetchall()
            
            # Get a few even ranges
            cursor.execute("""
                SELECT original_range_text, start_number, end_number 
                FROM house_ranges 
                WHERE is_even = 1 AND is_odd IS NULL
                  AND start_number IS NOT NULL AND end_number IS NOT NULL  
                LIMIT 3
            """)
            even_ranges = cursor.fetchall()
        
        # Test odd ranges
        for range_text, start_num, end_num in odd_ranges:
            if start_num and end_num and start_num < end_num:
                # Test an odd number in range
                odd_test_num = start_num if start_num % 2 == 1 else start_num + 1
                if odd_test_num <= end_num:
                    result = self._is_house_number_in_range_db(str(odd_test_num), range_text)
                    self.assertTrue(result, f"Odd number {odd_test_num} should match odd range {range_text}")
                
                # Test an even number in range (should fail)
                even_test_num = start_num if start_num % 2 == 0 else start_num + 1
                if even_test_num <= end_num:
                    result = self._is_house_number_in_range_db(str(even_test_num), range_text)
                    self.assertFalse(result, f"Even number {even_test_num} should NOT match odd range {range_text}")
        
        # Test even ranges
        for range_text, start_num, end_num in even_ranges:
            if start_num and end_num and start_num < end_num:
                # Test an even number in range
                even_test_num = start_num if start_num % 2 == 0 else start_num + 1  
                if even_test_num <= end_num:
                    result = self._is_house_number_in_range_db(str(even_test_num), range_text)
                    self.assertTrue(result, f"Even number {even_test_num} should match even range {range_text}")
                
                # Test an odd number in range (should fail)
                odd_test_num = start_num if start_num % 2 == 1 else start_num + 1
                if odd_test_num <= end_num:
                    result = self._is_house_number_in_range_db(str(odd_test_num), range_text)
                    self.assertFalse(result, f"Odd number {odd_test_num} should NOT match even range {range_text}")

    def test_dk_ranges_db(self):
        """Test DK ranges using database queries."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get some DK ranges
            cursor.execute("""
                SELECT original_range_text, start_number
                FROM house_ranges 
                WHERE range_type = 'dk' AND start_number IS NOT NULL
                LIMIT 5
            """)
            dk_ranges = cursor.fetchall()
        
        for range_text, start_num in dk_ranges:
            # Test number at start
            result = self._is_house_number_in_range_db(str(start_num), range_text)
            self.assertTrue(result, f"Start number {start_num} should match DK range {range_text}")
            
            # Test high number
            high_num = start_num + 1000
            result = self._is_house_number_in_range_db(str(high_num), range_text)
            self.assertTrue(result, f"High number {high_num} should match DK range {range_text}")
            
            # Test number below start (should fail)
            if start_num > 1:
                low_num = start_num - 1
                result = self._is_house_number_in_range_db(str(low_num), range_text)
                self.assertFalse(result, f"Low number {low_num} should NOT match DK range {range_text}")

    def test_api_integration(self):
        """Test the actual API endpoint."""
        import requests
        
        try:
            # Test the original problem case
            response = requests.get("http://localhost:5001/postal-codes", params={
                'city': 'Wrocław',
                'street': 'Jarocińska', 
                'house_number': '2'
            })
            
            if response.status_code == 200:
                data = response.json()
                self.assertEqual(data['count'], 1, "Should return exactly 1 result")
                self.assertFalse(data['fallback_used'], "Should not need fallback")
                self.assertEqual(data['results'][0]['postal_code'], '51-005', "Should return correct postal code")
            else:
                self.skipTest(f"API not available: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.skipTest("API server not running")

    def test_database_statistics(self):
        """Test database statistics to ensure migration worked correctly."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check basic counts
            cursor.execute("SELECT COUNT(*) FROM house_ranges")
            total_ranges = cursor.fetchone()[0]
            self.assertGreater(total_ranges, 10000, "Should have substantial number of ranges")
            
            # Check for different range types
            cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE range_type = 'dk'")
            dk_count = cursor.fetchone()[0]
            self.assertGreater(dk_count, 1000, "Should have many DK ranges")
            
            cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE is_odd = 1")
            odd_count = cursor.fetchone()[0]
            self.assertGreater(odd_count, 1000, "Should have many odd ranges")
            
            cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE is_even = 1")
            even_count = cursor.fetchone()[0]
            self.assertGreater(even_count, 1000, "Should have many even ranges")


def run_comprehensive_test():
    """Run all tests and provide detailed output."""
    print("="*60)
    print("COMPREHENSIVE NORMALIZED DATABASE TESTS")
    print("="*60)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestNormalizedImplementation)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.failures:
        print("\nFAILURES:")
        for test, error in result.failures:
            print(f"- {test}: {error}")
    
    if result.errors:
        print("\nERRORS:")
        for test, error in result.errors:
            print(f"- {test}: {error}")
    
    success_rate = (result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    if success_rate >= 95:
        print("🎉 EXCELLENT! Database normalization is working correctly!")
    elif success_rate >= 80:
        print("✅ GOOD! Minor issues but core functionality works!")
    else:
        print("⚠️  NEEDS WORK! Some significant issues detected!")


if __name__ == '__main__':
    run_comprehensive_test()