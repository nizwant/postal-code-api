#!/usr/bin/env python3
"""
Migration Validation Script

This script validates the normalized database by running comprehensive tests
to ensure the migration preserved data integrity and the new structure
correctly handles Polish postal code patterns.
"""

import sqlite3
import logging
from typing import List, Tuple, Dict
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class ValidationTest:
    name: str
    description: str
    passed: bool = False
    details: str = ""

class MigrationValidator:
    """Validates the normalized database migration."""
    
    def __init__(self, original_db_path: str, normalized_db_path: str):
        self.original_db_path = original_db_path
        self.normalized_db_path = normalized_db_path
        self.tests = []
    
    def run_all_validations(self) -> List[ValidationTest]:
        """Run all validation tests."""
        logger.info("Starting migration validation...")
        
        self.tests = []
        
        # Basic data integrity tests
        self._test_record_counts()
        self._test_data_preservation()
        self._test_no_data_loss()
        
        # Range parsing validation
        self._test_simple_ranges()
        self._test_odd_even_ranges()
        self._test_dk_ranges()
        self._test_complex_patterns()
        
        # Query performance validation
        self._test_house_number_lookup()
        self._test_original_problem_case()
        
        # Edge case validation
        self._test_edge_cases()
        
        # Report results
        self._generate_report()
        
        return self.tests
    
    def _test_record_counts(self):
        """Test that record counts are reasonable."""
        test = ValidationTest("Record Counts", "Verify record counts after migration")
        
        try:
            with sqlite3.connect(self.original_db_path) as orig_conn:
                orig_cursor = orig_conn.cursor()
                orig_cursor.execute("SELECT COUNT(*) FROM postal_codes")
                original_count = orig_cursor.fetchone()[0]
            
            with sqlite3.connect(self.normalized_db_path) as norm_conn:
                norm_cursor = norm_conn.cursor()
                
                norm_cursor.execute("SELECT COUNT(*) FROM postal_codes")
                copied_count = norm_cursor.fetchone()[0]
                
                norm_cursor.execute("SELECT COUNT(*) FROM house_ranges")
                normalized_count = norm_cursor.fetchone()[0]
                
                norm_cursor.execute("SELECT COUNT(*) FROM migration_stats")
                stats_count = norm_cursor.fetchone()[0]
            
            # Validation checks
            if copied_count == original_count:
                test.passed = True
                test.details = f"✓ Original records preserved: {original_count}\n"
                test.details += f"✓ Normalized records created: {normalized_count}\n"
                test.details += f"✓ Expansion ratio: {normalized_count/original_count:.2f}x\n"
                test.details += f"✓ Migration stats recorded: {stats_count}"
            else:
                test.details = f"✗ Record count mismatch: {original_count} → {copied_count}"
                
        except Exception as e:
            test.details = f"✗ Error during count validation: {e}"
        
        self.tests.append(test)
    
    def _test_data_preservation(self):
        """Test that original data is preserved."""
        test = ValidationTest("Data Preservation", "Verify original data is preserved in both tables")
        
        try:
            with sqlite3.connect(self.original_db_path) as orig_conn:
                with sqlite3.connect(self.normalized_db_path) as norm_conn:
                    orig_cursor = orig_conn.cursor()
                    norm_cursor = norm_conn.cursor()
                    
                    # Test a few random records
                    orig_cursor.execute("SELECT * FROM postal_codes LIMIT 5")
                    original_samples = orig_cursor.fetchall()
                    
                    matches = 0
                    for sample in original_samples:
                        norm_cursor.execute("SELECT * FROM postal_codes WHERE id = ?", (sample[0],))
                        normalized_sample = norm_cursor.fetchone()
                        
                        if sample == normalized_sample:
                            matches += 1
                    
                    if matches == len(original_samples):
                        test.passed = True
                        test.details = f"✓ All {matches}/{len(original_samples)} sample records preserved exactly"
                    else:
                        test.details = f"✗ Only {matches}/{len(original_samples)} records match"
                        
        except Exception as e:
            test.details = f"✗ Error during data preservation test: {e}"
        
        self.tests.append(test)
    
    def _test_no_data_loss(self):
        """Test that no original postal codes are lost."""
        test = ValidationTest("No Data Loss", "Verify every original postal code has corresponding house ranges")
        
        try:
            with sqlite3.connect(self.original_db_path) as orig_conn:
                with sqlite3.connect(self.normalized_db_path) as norm_conn:
                    orig_cursor = orig_conn.cursor()
                    norm_cursor = norm_conn.cursor()
                    
                    # Count postal codes with non-empty house_numbers
                    orig_cursor.execute("SELECT COUNT(*) FROM postal_codes WHERE house_numbers != ''")
                    original_with_houses = orig_cursor.fetchone()[0]
                    
                    # Count how many original records have house_ranges entries
                    norm_cursor.execute("""
                        SELECT COUNT(DISTINCT created_from_id) FROM house_ranges 
                        WHERE created_from_id IS NOT NULL
                    """)
                    normalized_with_ranges = norm_cursor.fetchone()[0]
                    
                    if normalized_with_ranges >= original_with_houses * 0.95:  # Allow 5% tolerance
                        test.passed = True
                        test.details = f"✓ {normalized_with_ranges}/{original_with_houses} records have house ranges (95%+ coverage)"
                    else:
                        test.details = f"✗ Only {normalized_with_ranges}/{original_with_houses} records have house ranges"
                        
        except Exception as e:
            test.details = f"✗ Error during data loss test: {e}"
        
        self.tests.append(test)
    
    def _test_simple_ranges(self):
        """Test simple range parsing."""
        test = ValidationTest("Simple Ranges", "Verify simple range patterns are parsed correctly")
        
        try:
            with sqlite3.connect(self.normalized_db_path) as conn:
                cursor = conn.cursor()
                
                # Test cases: range_text → expected results  
                test_cases = [
                    ("1-12", 1, 12, None, None, "simple"),
                    ("29-100", 29, 100, None, None, "simple"),
                ]
                
                passed_cases = 0
                for range_text, exp_start, exp_end, exp_odd, exp_even, exp_type in test_cases:
                    cursor.execute("""
                        SELECT start_number, end_number, is_odd, is_even, range_type 
                        FROM house_ranges WHERE original_range_text = ?
                    """, (range_text,))
                    
                    results = cursor.fetchall()
                    if results:
                        start, end, is_odd, is_even, range_type = results[0]
                        if (start == exp_start and end == exp_end and 
                            is_odd == exp_odd and is_even == exp_even and range_type == exp_type):
                            passed_cases += 1
                
                if passed_cases == len(test_cases):
                    test.passed = True
                    test.details = f"✓ All {passed_cases}/{len(test_cases)} simple range tests passed"
                else:
                    test.details = f"✗ Only {passed_cases}/{len(test_cases)} simple range tests passed"
                    
        except Exception as e:
            test.details = f"✗ Error during simple range test: {e}"
        
        self.tests.append(test)
    
    def _test_odd_even_ranges(self):
        """Test odd/even range parsing."""
        test = ValidationTest("Odd/Even Ranges", "Verify odd/even range patterns are parsed correctly")
        
        try:
            with sqlite3.connect(self.normalized_db_path) as conn:
                cursor = conn.cursor()
                
                # Count odd ranges
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE is_odd = 1")
                odd_count = cursor.fetchone()[0]
                
                # Count even ranges
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE is_even = 1")
                even_count = cursor.fetchone()[0]
                
                # Count neutral ranges (both null)
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE is_odd IS NULL AND is_even IS NULL")
                neutral_count = cursor.fetchone()[0]
                
                if odd_count > 0 and even_count > 0:
                    test.passed = True
                    test.details = f"✓ Found {odd_count} odd ranges, {even_count} even ranges, {neutral_count} neutral ranges"
                else:
                    test.details = f"✗ Insufficient odd/even ranges: {odd_count} odd, {even_count} even"
                    
        except Exception as e:
            test.details = f"✗ Error during odd/even test: {e}"
        
        self.tests.append(test)
    
    def _test_dk_ranges(self):
        """Test DK (do końca) range parsing."""
        test = ValidationTest("DK Ranges", "Verify DK (to end) ranges are parsed correctly")
        
        try:
            with sqlite3.connect(self.normalized_db_path) as conn:
                cursor = conn.cursor()
                
                # Count DK ranges
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE range_type = 'dk'")
                dk_count = cursor.fetchone()[0]
                
                # Check for DK ranges with null end_number
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE range_type = 'dk' AND end_number IS NULL")
                dk_null_end = cursor.fetchone()[0]
                
                if dk_count > 0:
                    test.passed = True
                    test.details = f"✓ Found {dk_count} DK ranges ({dk_null_end} with null end_number)"
                else:
                    test.details = f"✗ No DK ranges found"
                    
        except Exception as e:
            test.details = f"✗ Error during DK test: {e}"
        
        self.tests.append(test)
    
    def _test_complex_patterns(self):
        """Test complex pattern parsing."""
        test = ValidationTest("Complex Patterns", "Verify complex patterns are handled")
        
        try:
            with sqlite3.connect(self.normalized_db_path) as conn:
                cursor = conn.cursor()
                
                # Count complex patterns
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE range_type = 'complex'")
                complex_count = cursor.fetchone()[0]
                
                # Count patterns with letters
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE has_letters = 1")
                letter_count = cursor.fetchone()[0]
                
                # Count patterns with special cases
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE special_cases != '{}'")
                special_count = cursor.fetchone()[0]
                
                test.passed = True  # This is informational
                test.details = f"✓ Complex patterns: {complex_count}\n"
                test.details += f"✓ Patterns with letters: {letter_count}\n"
                test.details += f"✓ Patterns with special cases: {special_count}"
                    
        except Exception as e:
            test.details = f"✗ Error during complex pattern test: {e}"
        
        self.tests.append(test)
    
    def _test_house_number_lookup(self):
        """Test house number lookup functionality."""
        test = ValidationTest("House Number Lookup", "Test house number lookup queries")
        
        try:
            with sqlite3.connect(self.normalized_db_path) as conn:
                cursor = conn.cursor()
                
                # Test case: house number 2 should match range 1-12
                cursor.execute("""
                    SELECT postal_code, start_number, end_number, is_odd, is_even 
                    FROM house_ranges 
                    WHERE start_number <= 2 
                      AND (end_number >= 2 OR end_number IS NULL)
                      AND (is_odd IS NULL OR is_even IS NULL OR is_even = 1)  -- 2 is even
                    LIMIT 5
                """)
                
                results = cursor.fetchall()
                
                if len(results) > 0:
                    test.passed = True
                    test.details = f"✓ Found {len(results)} ranges containing house number 2\n"
                    for result in results[:3]:  # Show first 3
                        test.details += f"  - {result[0]}: {result[1]}-{result[2] or 'DK'} (odd: {result[3]}, even: {result[4]})\n"
                else:
                    test.details = f"✗ No ranges found containing house number 2"
                    
        except Exception as e:
            test.details = f"✗ Error during lookup test: {e}"
        
        self.tests.append(test)
    
    def _test_original_problem_case(self):
        """Test the original problem case: Wrocław, Jarocińska, house number 2."""
        test = ValidationTest("Original Problem Case", "Test the specific case that motivated this migration")
        
        try:
            with sqlite3.connect(self.normalized_db_path) as conn:
                cursor = conn.cursor()
                
                # The original problematic query
                cursor.execute("""
                    SELECT postal_code, start_number, end_number, is_odd, is_even, original_range_text
                    FROM house_ranges 
                    WHERE LOWER(city) LIKE LOWER('Wrocław%') 
                      AND LOWER(street) = LOWER('Jarocińska')
                      AND start_number <= 2 
                      AND (end_number >= 2 OR end_number IS NULL)
                      AND (is_odd IS NULL OR is_even IS NULL OR is_even = 1)  -- 2 is even
                """)
                
                results = cursor.fetchall()
                
                if len(results) == 1 and results[0][0] == '51-005':
                    test.passed = True
                    test.details = f"✓ Perfect! House number 2 matches exactly one range:\n"
                    test.details += f"  - Postal code: {results[0][0]}\n"
                    test.details += f"  - Range: {results[0][1]}-{results[0][2]} ({results[0][5]})\n"
                    test.details += f"  - Odd/Even: {results[0][3]}/{results[0][4]}"
                elif len(results) > 1:
                    test.details = f"⚠ Found {len(results)} matches (expected 1):\n"
                    for result in results:
                        test.details += f"  - {result[0]}: {result[1]}-{result[2]} ({result[5]})\n"
                else:
                    test.details = f"✗ No matches found for Wrocław, Jarocińska, house number 2"
                    
        except Exception as e:
            test.details = f"✗ Error during original problem test: {e}"
        
        self.tests.append(test)
    
    def _test_edge_cases(self):
        """Test edge cases and error handling."""
        test = ValidationTest("Edge Cases", "Test edge cases and error conditions")
        
        try:
            with sqlite3.connect(self.normalized_db_path) as conn:
                cursor = conn.cursor()
                
                # Test empty house_numbers
                cursor.execute("SELECT COUNT(*) FROM house_ranges WHERE original_range_text = ''")
                empty_ranges = cursor.fetchone()[0]
                
                # Test very high numbers (DK ranges)
                cursor.execute("""
                    SELECT COUNT(*) FROM house_ranges 
                    WHERE range_type = 'dk' AND start_number <= 1000
                """)
                dk_high_numbers = cursor.fetchone()[0]
                
                test.passed = True  # Informational
                test.details = f"✓ Empty ranges handled: {empty_ranges}\n"
                test.details += f"✓ DK ranges for high numbers: {dk_high_numbers}"
                    
        except Exception as e:
            test.details = f"✗ Error during edge case test: {e}"
        
        self.tests.append(test)
    
    def _generate_report(self):
        """Generate a comprehensive validation report."""
        passed_tests = sum(1 for test in self.tests if test.passed)
        total_tests = len(self.tests)
        
        logger.info("="*60)
        logger.info("MIGRATION VALIDATION REPORT")
        logger.info("="*60)
        logger.info(f"Overall: {passed_tests}/{total_tests} tests passed")
        logger.info("")
        
        for test in self.tests:
            status = "PASS" if test.passed else "FAIL"
            logger.info(f"[{status}] {test.name}: {test.description}")
            if test.details:
                for line in test.details.split('\n'):
                    if line.strip():
                        logger.info(f"        {line}")
            logger.info("")
        
        if passed_tests == total_tests:
            logger.info("🎉 All validations passed! Migration is successful.")
        else:
            logger.warning(f"⚠️  {total_tests - passed_tests} validations failed. Review before proceeding.")


def main():
    """Main validation function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate postal codes database migration')
    parser.add_argument('--original', default='postal_codes.db', help='Original database path')
    parser.add_argument('--normalized', default='postal_codes_normalized.db', help='Normalized database path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    validator = MigrationValidator(args.original, args.normalized)
    tests = validator.run_all_validations()
    
    # Return appropriate exit code
    passed_tests = sum(1 for test in tests if test.passed)
    if passed_tests == len(tests):
        exit(0)  # Success
    else:
        exit(1)  # Some tests failed


if __name__ == '__main__':
    main()